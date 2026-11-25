"""Gera, por questao, um recorte fiel (imagem) do enunciado+alternativas, com posicoes das alternativas.
Marca 'precisa_img' quando ha formulas/fracoes/expoentes ou alternativas vazias."""
import sys, re, os, json, statistics
import pdfplumber
sys.path.insert(0, os.path.dirname(__file__))
import parse_exam as P

DPI = 160
K = DPI / 72.0
ALT = re.compile(r'^\s*\(([A-E])\)')
QST = re.compile(r'^\s*0?(\d{1,2})\.\s')
INSTR = re.compile(r'(?i)(responder\s+(às|as|à|a)\s+quest|quest[õo]es?\s+(de\s+)?(n[úu]meros?\s+)?\d{1,2}\s*(a|e)\s*\d{1,2})')

def is_heading(t):
    t = t.strip()
    if len(t) > 45 or re.search(r'[.,;:?!()\d]', t): return False
    if t.lower().replace(' ', '') in {k.replace(' ', '') for k in P.DISC_MAP}: return True
    return P.letters_sig(t) in P.HEAD_SIGS

def is_foot(t, top, H=841.9):
    t = t.strip()
    if not t: return False
    if any(r.search(t) for r in P.FOOT_RES[:-1]): return True
    return bool(re.fullmatch(r'\d{1,2}', t) and top > H - 58)

def frames_of(pdf, figs):
    out = []
    for pno, p in enumerate(pdf.pages, 1):
        if pno < 2: continue
        W, H = float(p.width), float(p.height); mid = W / 2
        gut = [c for c in p.chars if 55 < c['top'] < H - 55 and mid - 7 < (c['x0'] + c['x1']) / 2 < mid + 7 and c['text'].strip()]
        fb = [f['bbox'] for f in figs.get(str(pno), [])]
        wide = any(f[0] < mid - 20 and f[2] > mid + 20 and (f[2] - f[0]) > 0.5 * W for f in fb)
        rtxt = [c for c in p.chars if c['text'].strip() and 55 < c['top'] < H - 55 and c['x0'] > mid + 20 and not any(f[0] - 2 <= c['x0'] and c['x1'] <= f[2] + 2 and f[1] - 2 <= c['top'] and c['bottom'] <= f[3] + 2 for f in fb)]
        cols = [(0, W)] if (len(gut) >= 20 or (wide and len(rtxt) < 120)) else [(0, mid), (mid, W)]
        for (x0, x1) in cols:
            out.append((pno, p, x0, x1, 15.0, H - 4.0))
    return out

def run(pdfpath, name, outdir, nq, figs):
    os.makedirs(outdir, exist_ok=True)
    pdf = pdfplumber.open(pdfpath)
    frames = frames_of(pdf, figs)
    flines = []
    for (pno, p, x0, x1, yt, yb) in frames:
        ls = p.crop((x0, yt, x1, yb)).extract_text_lines(x_tolerance=1.5, y_tolerance=2)
        flines.append(ls)
    # localiza inicio de cada questao
    starts = {}; fi = 0; expected = 1
    for i, ls in enumerate(flines):
        for l in ls:
            m = QST.match(l['text'])
            if m and int(m.group(1)) == expected and l['x0'] < frames[i][2] + 45:
                starts[expected] = (i, l['top']); expected += 1
                if expected > nq: break
        if expected > nq: break
    res = {}
    nums = sorted(starts)
    for n in nums:
        i0, t0 = starts[n]
        # fim = inicio da proxima questao, ou cabecalho/instrucao
        end = None
        nxt = starts.get(n + 1)
        pieces = []
        i = i0
        while True:
            pno, p, x0, x1, yt, yb = frames[i]
            top = t0 if i == i0 else yt
            bot = yb
            cut = None
            for l in flines[i]:
                if l['top'] <= top + 8: continue
                if is_foot(l['text'], l['top']): cut = l['top']; break
                if nxt and nxt[0] == i and abs(l['top'] - nxt[1]) < 1: cut = l['top']; break
                if INSTR.search(l['text']) and l['text'][:1].isupper() and not ALT.match(l['text']): cut = l['top']; break
                if is_heading(l['text']): cut = l['top']; break
            if cut is not None:
                bot = cut - 3; done = True
            else:
                done = bool(nxt and nxt[0] == i) 
            pieces.append((i, top - 3, bot, done and cut is not None) )
            if cut is not None or (nxt and nxt[0] == i) or i + 1 >= len(frames) or (pieces and len(pieces) >= 3):
                break
            if nxt is None and i + 1 < len(frames):
                # ultima questao: nao atravessa para outros frames
                break
            i += 1
        # recorta e empilha
        crops = []; altpos = {}; y = 0; flag = False; reasons = []; vec = []; qfig = {'stem': [], 'alt': []}; pidx = -1; Apos = None; pfigs = []
        for (fi_, ta, tb, _) in pieces:
            pno, p, x0, x1, yt, yb = frames[fi_]
            ta = max(ta, 0)
            if tb - ta < 6: continue
            pidx += 1
            reg = p.crop((x0 + 1, ta, x1 - 1, tb))
            # sinais de formula
            fb = [f['bbox'] for f in figs.get(str(pno), [])]
            def infig(o):
                return any(o['x0'] >= a0 - 24 and o['x1'] <= a2 + 24 and o['top'] >= a1 - 16 and o['bottom'] <= a3 + 16 for (a0, a1, a2, a3) in fb)
            def vecfrac(o):
                w = o['x1'] - o['x0']; h = o['bottom'] - o['top']
                if w > 90 or h > 2.5 or w < 3: return None
                cu = [c for c in reg.curves if o['x0'] - 3 <= (c['x0'] + c['x1']) / 2 <= o['x1'] + 3 and (c['bottom'] <= o['top'] + 1.5 and c['bottom'] > o['top'] - 15 or c['top'] >= o['bottom'] - 1.5 and c['top'] < o['bottom'] + 15)]
                return o['top'] if cu else None
            for o in reg.lines + reg.rects:
                if infig(o): continue
                yb_ = vecfrac(o)
                if yb_ is not None: vec.append((fi_, yb_))
            curv = [o for o in reg.curves if not infig(o) and (o['bottom'] - o['top']) >= 17 and (o['x1'] - o['x0']) < 60]
            for o in curv: vec.append((fi_, o['top']))
            for l in flines[fi_]:
                if ta - 1 <= l['top'] <= tb:
                    m = ALT.match(l['text'])
                    if m and m.group(1) == 'A' and Apos is None: Apos = (pidx, l['top'])
                    if m and m.group(1) not in altpos:
                        altpos[m.group(1)] = (l['top'] - ta) * K + y - 2
            for fj in figs.get(str(pno), []):
                bx = fj['bbox']; cx_ = (bx[0] + bx[2]) / 2; cy_ = (bx[1] + bx[3]) / 2
                if x0 - 2 <= cx_ <= x1 + 2 and ta - 2 <= cy_ <= tb + 2:
                    pfigs.append((pidx, cy_, f'{name}/{fj["f"]}'))
            im = reg.to_image(resolution=DPI).original.convert('RGB')
            crops.append(im); y += im.height
        if not crops: continue
        from PIL import Image
        Wt = max(c.width for c in crops)
        canvas = Image.new('RGB', (Wt, y), 'white'); yy = 0
        for c in crops:
            canvas.paste(c, (0, yy)); yy += c.height
        # zona: vetor acima do topo da alternativa A => enunciado; abaixo => alternativas
        vs = [t for (fi_, t) in vec]
        ytop_alt = None
        if 'A' in altpos:
            ytop_alt = altpos['A']
        vec_stem = vec_alt = False
        if vec:
            # converte posicao de cada vetor para y do canvas
            acc = 0; offs = {}
            for (fi_, ta, tb, _) in pieces:
                offs[fi_] = (ta, acc); acc += int(((tb - max(ta, 0)) * K)) if tb - ta >= 6 else 0
            for (fi_, t) in vec:
                if fi_ in offs:
                    yy = (t - offs[fi_][0]) * K + offs[fi_][1]
                    if ytop_alt is None or yy < ytop_alt: vec_stem = True
                    else: vec_alt = True
        for (pj, cy_, nm) in pfigs:
            isalt = Apos is not None and (pj > Apos[0] or (pj == Apos[0] and cy_ >= Apos[1]))
            qfig['alt' if isalt else 'stem'].append(nm)
        fn = f'q{n:02d}.png'
        canvas.save(os.path.join(outdir, fn), optimize=True)
        res[n] = {'f': fn, 'w': Wt, 'h': y, 'alts': {k: round(v) for k, v in altpos.items()}, 'figs': qfig, 'flag': vec_stem or vec_alt, 'vstem': vec_stem, 'valt': vec_alt, 'why': reasons[:3]}
    json.dump(res, open(os.path.join(outdir, 'q.json'), 'w'))
    return res

if __name__ == '__main__':
    pdfpath, name, outdir, nq = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    figs = json.load(open(f'work/figs/{name}/figs.json'))
    r = run(pdfpath, name, outdir, nq, figs)
    print(name, len(r), 'questoes recortadas;', sum(v['flag'] for v in r.values()), 'marcadas')
