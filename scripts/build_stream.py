"""Constroi, para cada PDF de prova, um fluxo de linhas em ordem de leitura (coluna esquerda, depois direita),
com marcadores de disciplina (@@H:...), imagens (@@IMG) e quebra de pagina (@@PAGE n).
Uso: python3 -I build_stream.py <pasta_pdfs> <pasta_saida> [nome_sem_extensao ...]
"""
import sys, os, glob, json, re, unicodedata
import pdfplumber
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pageprep

HEAD_VOCAB = [
    'língua portuguesa e interpretação de texto', 'língua portuguesa', 'matemática', 'conhecimentos gerais',
    'conhecimentos específicos', 'história geral', 'história do brasil', 'geografia geral', 'geografia do brasil',
    'atualidades', 'noções básicas de informática', 'noções de informática', 'noções de administração pública',
    'noções de direito', 'direitos humanos', 'informática', 'redação',
]

def norm(s):
    return re.sub(r'\s+', ' ', s.strip().lower())

def clean_line(t):
    t = t.replace('­', '')
    t = re.sub(r'\(cid:\d+\)', '', t)
    return t.rstrip()

def is_heading_text(t):
    n = norm(t)
    return n in HEAD_VOCAB

def process(path, figs=None, name=''):
    figs = figs or {}
    items = []   # (page, col, top, kind, text)
    with pdfplumber.open(path) as pdf:
        for pno, p in enumerate(pdf.pages, 1):
            W, H = float(p.width), float(p.height)
            mid = W / 2
            try:
                pageprep.prep(p, [f['bbox'] for f in figs.get(str(pno), [])])
            except Exception as e:
                print('prep falhou', pno, e)
            # --- cabecalhos de disciplina (linha cheia) ---
            heads = []   # (col, top, bottom, x0, x1, label)
            try:
                full = p.extract_text_lines(x_tolerance=1.5, y_tolerance=2)
            except Exception:
                full = []
            for ln in full:
                chars = ln['chars']
                if not chars:
                    continue
                bold = sum('bold' in c['fontname'].lower() for c in chars) / len(chars)
                txt = ln['text'].strip()
                if len(txt) > 52:
                    continue
                # linha inteira e um titulo (pode cruzar o meio da pagina)
                left = ''.join(c['text'] for c in chars if (c['x0'] + c['x1']) / 2 < mid).strip()
                right = ''.join(c['text'] for c in chars if (c['x0'] + c['x1']) / 2 >= mid).strip()
                cand = []
                if is_heading_text(re.sub(r'\s+', ' ', txt)):
                    cx = (ln['x0'] + ln['x1']) / 2
                    spans = ln['x0'] < mid < ln['x1']
                    cand.append(('L' if (cx < mid or spans) else 'R', txt))
                else:
                    if left and is_heading_text(left):
                        cand.append(('L', left))
                    if right and is_heading_text(right):
                        cand.append(('R', right))
                    # titulo duplo na mesma linha sem separar por coluna (ex.: 'geografia geral geografia do brasil')
                for col, label in cand:
                    heads.append((col, ln['top'], ln['bottom'], ln['x0'], ln['x1'], label))
            # remove os caracteres dos titulos antes de cortar as colunas
            fb = [f['bbox'] for f in figs.get(str(pno), [])]
            def keep(obj):
                if obj.get('object_type') != 'char':
                    return True
                for (_, t, b, x0, x1, _) in heads:
                    if obj['top'] >= t - 1 and obj['bottom'] <= b + 1 and obj['x0'] >= x0 - 1 and obj['x1'] <= x1 + 1:
                        return False
                return True
            pf = p.filter(keep) if heads else p
            items.append((pno, 'L', -1.0, 'page', str(pno)))
            cross = [c for c in p.chars if 55 < c['top'] < H - 55 and mid - 7 < (c['x0'] + c['x1']) / 2 < mid + 7 and c['text'].strip()]
            wide = any(f[0] < mid - 20 and f[2] > mid + 20 and (f[2] - f[0]) > 0.5 * W for f in fb)
            rtxt = [c for c in p.chars if c['text'].strip() and 55 < c['top'] < H - 55 and c['x0'] > mid + 20 and not any(f[0] - 2 <= c['x0'] and c['x1'] <= f[2] + 2 and f[1] - 2 <= c['top'] and c['bottom'] <= f[3] + 2 for f in fb)]
            single = len(cross) >= 20 or (wide and len(rtxt) < 120)
            if single:
                heads = [('L',) + h[1:] for h in heads]
            for col, box in ((('L', (0, 0, W, H)),) if single else (('L', (0, 0, mid, H)), ('R', (mid, 0, W, H)))):
                try:
                    lines = pf.crop(box).extract_text_lines(x_tolerance=1.5, y_tolerance=2)
                except Exception:
                    lines = []
                long_ = [l for l in lines if len(l['text']) >= 25]
                left = min((l['x0'] for l in long_), default=None)
                right = max((l['x1'] for l in long_), default=None)
                for ln in lines:
                    if any(ln['x0'] >= a0 - 2 and ln['x1'] <= a2 + 2 and ln['top'] >= a1 - 2 and ln['bottom'] <= a3 + 2 for (a0, a1, a2, a3) in fb):
                        continue
                    txt = clean_line(ln['text'])
                    if re.fullmatch(r'\s*\d{1,2}\s*', txt) and (ln['top'] > H - 75 or ln['top'] < 45):
                        continue
                    if left is not None:
                        if ln['x0'] > left + 6:
                            txt = '\x01' + txt
                        if ln['x1'] < right - 28:
                            txt = txt + '\x02'
                    items.append((pno, col, ln['top'], 'line', txt))
            for (col, t, b, x0, x1, label) in heads:
                items.append((pno, col, t - 0.5, 'head', norm(label)))
            for f in figs.get(str(pno), []):
                a0, a1, a2, a3 = f['bbox']
                cx = (a0 + a2) / 2
                col = 'L' if single or a0 < mid - 5 or (a2 - a0) > 0.7 * W else 'R'
                items.append((pno, col, a1 - 0.25, 'img', f'fig:{name}/{f["f"]}'))
    order = {'L': 0, 'R': 1}
    items.sort(key=lambda x: (x[0], order[x[1]] if x[3] != 'page' else -1, x[2]))
    out = []
    for pno, col, top, kind, text in items:
        if kind == 'page':
            out.append(f'@@PAGE {text}')
        elif kind == 'head':
            out.append(f'@@H:{text}')
        elif kind == 'img':
            out.append(f'@@IMG {text}')
        else:
            out.append(text)
    return out

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    os.makedirs(dst, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(src, '*prova*.pdf'))):
        name = os.path.basename(f)[:-4]
        if only and name not in only:
            continue
        figs = json.load(open(os.path.join(sys.argv[3] if False else 'work/figs', name, 'figs.json'))) if os.path.exists(os.path.join('work/figs', name, 'figs.json')) else {}
        lines = process(f, figs, name)
        open(os.path.join(dst, name + '.txt'), 'w', encoding='utf8').write('\n'.join(lines))
        print('ok', name, len(lines))
