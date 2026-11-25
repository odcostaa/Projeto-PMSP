import re
"""Detecta figuras (imagens rasters e graficos/tabelas vetoriais) por pagina e recorta PNG.
Uso: python3 -I figs.py <pasta_pdfs> <saida> [nome ...]   -> saida/<nome>/figs.json + png"""
import sys, os, glob, json, re
import pdfplumber

def overlap(a, b, pad, pady=None):
    pady = pad if pady is None else pady
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pady < b[1] or b[3] + pady < a[1])

def _is_small_bar(p, o):
    w = o['x1'] - o['x0']; h = o['bottom'] - o['top']
    return 3 <= w <= 90 and h <= 2.5

def _isolated(p, o):
    rs = [r for k in ('lines', 'rects') for r in getattr(p, k) if (r['bottom'] - r['top']) <= 2.5]
    return sum(1 for r in rs if r is not o and r['x0'] <= o['x1'] + 3 and r['x1'] >= o['x0'] - 3 and 4 < abs(r['top'] - o['top']) < 40) < 2

def detect(p):
    W, H = float(p.width), float(p.height)
    objs = []
    for im in p.images:
        w = im['x1'] - im['x0']; h = im['bottom'] - im['top']
        if w > W * 1.1 or h > H * 0.85 or w < 25 or h < 25:   # marca d'agua / lixo
            continue
        objs.append((im['x0'], im['top'], im['x1'], im['bottom'], 'img'))
    smalls = []
    for k in ('rects', 'curves', 'lines'):
        for o in getattr(p, k):
            x0, t, x1, b = o['x0'], o['top'], o['x1'], o['bottom']
            if t < 55 or b > H - 50:
                continue
            if k != 'curves' and _is_small_bar(p, o) and _isolated(p, o):
                continue
            if (x1 - x0) > W * 0.9 and (b - t) < 3:     # fios horizontais de pagina
                continue
            if (x1 - x0) < 0.5 and (b - t) < 0.5:
                continue
            objs.append((x0, t, x1, b, k))
    # agrupa
    mathc = [o for o in objs if o[4] == 'curves' and (o[2] - o[0]) < 40 and 17 <= (o[3] - o[1]) < 70]
    cl = []
    for o in objs:
        box = list(o[:4]); kinds = {o[4]}; n = 1
        merged = True
        while merged:
            merged = False
            for c in cl:
                rule = kinds <= {'lines', 'rects'} and c['k'] <= {'lines', 'rects'}
                if overlap(box, c['b'], 5, 85 if rule else 5):
                    box = [min(box[0], c['b'][0]), min(box[1], c['b'][1]), max(box[2], c['b'][2]), max(box[3], c['b'][3])]
                    kinds |= c['k']; n += c['n']; cl.remove(c); merged = True; break
        cl.append({'b': box, 'k': kinds, 'n': n})
    res = []
    for c in cl:
        x0, t, x1, b = c['b']; w = x1 - x0; h = b - t
        if w < 50 or h < 30:
            continue
        if 'img' not in c['k'] and c['n'] < 4 and not ({'rects', 'curves'} & c['k']):
            continue   # so linhas soltas
        # texto dentro: se for quase so texto corrido, nao e figura
        inside = [ch for ch in p.chars if x0 - 1 <= ch['x0'] and ch['x1'] <= x1 + 1 and t - 1 <= ch['top'] and ch['bottom'] <= b + 1]
        if 'img' not in c['k'] and len(inside) > 450:
            continue
        if 'img' not in c['k'] and h < 32:
            continue   # linhas de texto com caixa/sublinhado (ex.: alternativas)
        if 'img' not in c['k']:
            # rotulos soltos (A, B, C...) logo fora da figura geometrica
            toks = []
            for ch in sorted([c for c in p.chars if c['text'].strip()], key=lambda c: (round(c['top'] / 3), c['x0'])):
                if toks and abs(toks[-1]['top'] - ch['top']) < 2.5 and 0 <= ch['x0'] - toks[-1]['x1'] < 2.2:
                    toks[-1].update(text=toks[-1]['text'] + ch['text'], x1=ch['x1'], bottom=max(toks[-1]['bottom'], ch['bottom']))
                else:
                    toks.append({'text': ch['text'], 'x0': ch['x0'], 'x1': ch['x1'], 'top': ch['top'], 'bottom': ch['bottom']})
            for tk in toks:
                if len(tk['text']) > 6: continue
                outside = not (x0 - 1 <= tk['x0'] and tk['x1'] <= x1 + 1 and t - 1 <= tk['top'] and tk['bottom'] <= b + 1)
                if not (outside and x0 - 22 <= tk['x0'] and tk['x1'] <= x1 + 22 and t - 14 <= tk['top'] and tk['bottom'] <= b + 14): continue
                nb = [o for o in toks if o is not tk and abs(o['top'] - tk['top']) < 2.5 and (0 <= tk['x0'] - o['x1'] < 9 or 0 <= o['x0'] - tk['x1'] < 9)]
                if nb: continue
                x0 = min(x0, tk['x0']); x1 = max(x1, tk['x1']); t = min(t, tk['top']); b = max(b, tk['bottom'])
        res.append((max(x0 - 4, 0), max(t - 4, 0), min(x1 + 4, W), min(b + 4, H), sorted(c['k'])))
    # curvas pequenas isoladas (chaves de sistemas, radicais...): une com o texto da mesma faixa vertical
    covered = lambda bb: any(not (bb[2] < r[0] or r[2] < bb[0] or bb[3] < r[1] or r[3] < bb[1]) for r in res)
    groups = []
    for o in sorted(mathc, key=lambda o: o[1]):
        bb = list(o[:4])
        if covered(bb): continue
        for g in groups:
            if abs(g[1] - bb[1]) < 6 or (bb[1] < g[3] and bb[3] > g[1]):
                g[0] = min(g[0], bb[0]); g[1] = min(g[1], bb[1]); g[2] = max(g[2], bb[2]); g[3] = max(g[3], bb[3]); break
        else:
            groups.append(bb)
    for g in groups:
        ch = [c for c in p.chars if g[1] - 2 <= (c['top'] + c['bottom']) / 2 <= g[3] + 2 and abs(((c['x0'] + c['x1']) / 2) - ((g[0] + g[2]) / 2)) < 260]
        # limita a mesma coluna do grupo
        colx0 = 0 if g[0] < W / 2 else W / 2; colx1 = W / 2 if g[0] < W / 2 else W
        ch = [c for c in ch if colx0 - 2 <= c['x0'] and c['x1'] <= colx1 + 2]
        if ch:
            g = [min(g[0], min(c['x0'] for c in ch)), min(g[1], min(c['top'] for c in ch)), max(g[2], max(c['x1'] for c in ch)), max(g[3], max(c['bottom'] for c in ch))]
        res.append((max(g[0] - 4, 0), max(g[1] - 3, 0), min(g[2] + 4, W), min(g[3] + 3, H), ['math']))
    return res

def refine(p, x0, t, x1, b, kinds):
    kinds = set(kinds)
    # paragrafo com lacunas sublinhadas nao e figura
    if not ({'img', 'curves'} & kinds):
        try:
            ls = p.crop((x0, t, x1, b)).extract_text_lines(x_tolerance=1.5, y_tolerance=2)
        except Exception:
            ls = []
        longl = [l for l in ls if len(l['text']) >= 38]
        if len(ls) >= 3 and len(longl) >= 3 and len(longl) >= 0.6 * len(ls):
            return None, None, None, None
    if not ({'img', 'curves'} & kinds) and (b - t) < 80:
        rr = [c for c in p.chars if c['text'].strip() and x1 - 1 <= c['x0'] <= x1 + 7 and t - 2 <= (c['top'] + c['bottom']) / 2 <= b + 2]
        if len(rr) >= 2: return None, None, None, None
    W, H = float(p.width), float(p.height)
    chars = [c for c in p.chars if c['text'].strip()]
    for _ in range(2):
        for c in chars:
            ow = min(c['x1'], x1) - max(c['x0'], x0); oh = min(c['bottom'], b) - max(c['top'], t)
            if ow <= 0 or oh <= 0: continue
            inside = c['x0'] >= x0 - 0.5 and c['x1'] <= x1 + 0.5 and c['top'] >= t - 0.5 and c['bottom'] <= b + 0.5
            if inside: continue
            if ow >= 0.4 * (c['x1'] - c['x0']) and oh >= 0.4 * (c['bottom'] - c['top']):
                nx0, nt, nx1, nb = min(x0, c['x0']), min(t, c['top']), max(x1, c['x1']), max(b, c['bottom'])
                if x0 - nx0 <= 40 and nx1 - x1 <= 40 and t - nt <= 22 and nb - b <= 22:
                    x0, t, x1, b = nx0, nt, nx1, nb
    # titulo centralizado logo acima (versalete) e legenda logo abaixo
    cx = (x0 + x1) / 2
    try:
        lines = p.extract_text_lines(x_tolerance=1.5, y_tolerance=2)
    except Exception:
        lines = []
    for l in lines:
        txt = l['text'].strip()
        if not txt or len(txt) > 80 or re.match(r'^(\d{1,2}\.|\([A-E]\))', txt): continue
        lc = (l['x0'] + l['x1']) / 2
        if abs(lc - cx) < 30 and (l['x1'] - l['x0']) < 420 and l['x0'] >= x0 - 120 and l['x1'] <= x1 + 120:
            if 0 <= t - l['bottom'] <= 16 and re.search(r'[A-ZÀ-Ú]', txt[:3]):
                t = min(t, l['top'] - 1); x0 = min(x0, l['x0'] - 2); x1 = max(x1, l['x1'] + 2)
    return x0, t, x1, b

def run(path, outdir):
    name = os.path.basename(path)[:-4]
    d = os.path.join(outdir, name); os.makedirs(d, exist_ok=True)
    info = {}
    with pdfplumber.open(path) as pdf:
        for pno, p in enumerate(pdf.pages, 1):
            lst = []
            dets = []
            for (x0, t, x1, b, kinds) in detect(p):
                x0, t, x1, b = refine(p, x0, t, x1, b, kinds)
                if x0 is None: continue
                dets.append((x0, t, x1, b, kinds))
            for k, (x0, t, x1, b, kinds) in enumerate(dets, 1):
                fn = f'p{pno:02d}_{k}.png'
                try:
                    p.crop((x0, t, x1, b)).to_image(resolution=130).save(os.path.join(d, fn))
                except Exception as e:
                    continue
                lst.append({'f': fn, 'bbox': [x0, t, x1, b], 'k': kinds})
            if lst: info[pno] = lst
    json.dump(info, open(os.path.join(d, 'figs.json'), 'w'))
    return name, sum(len(v) for v in info.values())

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]; only = set(sys.argv[3:])
    for f in sorted(glob.glob(os.path.join(src, '*prova*.pdf'))):
        n = os.path.basename(f)[:-4]
        if only and n not in only: continue
        print(*run(f, dst))
