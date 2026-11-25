"""Recorta a regiao inteira de uma questao (enunciado + alternativas) de um PDF -> PNG."""
import sys, re, json, pdfplumber
def crop_question(pdfpath, page, num, out, last_num=None):
    with pdfplumber.open(pdfpath) as pdf:
        p = pdf.pages[page - 1]
        W, H = float(p.width), float(p.height); mid = W / 2
        gut = [c for c in p.chars if 55 < c['top'] < H - 55 and mid - 7 < (c['x0'] + c['x1']) / 2 < mid + 7 and c['text'].strip()]
        cols = [(0, W)] if len(gut) >= 20 else [(0, mid), (mid, W)]
        pat = re.compile(r'^\s*(\d{1,2})\.\s')
        for (x0, x1) in cols:
            lines = p.crop((x0, 0, x1, H)).extract_text_lines(x_tolerance=1.5, y_tolerance=2)
            starts = [(l['top'], int(pat.match(l['text']).group(1))) for l in lines if pat.match(l['text']) and l['x0'] < x0 + 40]
            mine = [t for t, n in starts if n == num]
            if not mine: continue
            top = mine[0]
            nxt = [t for t, n in starts if t > top + 5]
            bot = min(nxt) - 4 if nxt else H - 60
            # corta tambem em cabecalho de disciplina / instrucao de grupo seguinte
            for l in lines:
                if l['top'] > top + 30 and re.match(r'(?i)^(leia|observe|considere)\b.*(responder|quest)', l['text']) and l['top'] < bot:
                    bot = l['top'] - 4; break
            p.crop((x0 + 2, max(top - 3, 0), x1 - 2, min(bot, H))).to_image(resolution=130).save(out)
            return True
    return False
