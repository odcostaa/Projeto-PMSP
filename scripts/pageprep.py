"""Pre-processa uma pagina do pdfplumber: reconstroi fracoes empilhadas (a/b) e expoentes em texto."""
import re, statistics, copy

SUP = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')

def _cx(c): return (c['x0'] + c['x1']) / 2

def prep(p, figboxes=()):
    objs = p.objects
    chars = objs.get('char', [])
    if not chars: return 0
    def infig(o):
        return any(o['x0'] >= a0 - 3 and o['x1'] <= a2 + 3 and o['top'] >= a1 - 3 and o['bottom'] <= a3 + 3 for (a0, a1, a2, a3) in figboxes)
    bars = []
    for k in ('line', 'rect'):
        for o in objs.get(k, []):
            w = o['x1'] - o['x0']; h = o['bottom'] - o['top']
            if 3 <= w <= 90 and h <= 2.5 and not infig(o): bars.append((k, o))
    allr = [o for k in ('line', 'rect') for o in objs.get(k, []) if (o['bottom'] - o['top']) <= 2.5]
    def isolated(o):
        return sum(1 for r in allr if r is not o and r['x0'] <= o['x1'] + 3 and r['x1'] >= o['x0'] - 3 and 4 < abs(r['top'] - o['top']) < 40) < 2
    bars = [(k, o) for (k, o) in bars if isolated(o)]
    used = set(); new = []; rm_bars = []; nfrac = 0
    ids = {id(c): c for c in chars}
    for (k, o) in bars:
        top_c = [c for c in chars if id(c) not in used and c['text'].strip() and o['x0'] - 3 <= _cx(c) <= o['x1'] + 3 and o['top'] - 15 < c['bottom'] <= o['top'] + 1.5]
        bot_c = [c for c in chars if id(c) not in used and c['text'].strip() and o['x0'] - 3 <= _cx(c) <= o['x1'] + 3 and o['bottom'] - 1.5 <= c['top'] < o['bottom'] + 15]
        if not top_c or not bot_c: continue
        # so a linha mais proxima acima/abaixo
        ty = max(c['bottom'] for c in top_c); top_c = [c for c in top_c if c['bottom'] > ty - 6]
        by = min(c['top'] for c in bot_c); bot_c = [c for c in bot_c if c['top'] < by + 6]
        def join(cs):
            cs = sorted(cs, key=lambda c: c['x0']); s = ''; prev = None
            for c in cs:
                if prev is not None and c['x0'] - prev['x1'] > 0.3 * c['size']: s += ' '
                s += c['text']; prev = c
            return s.strip()
        num, den = join(top_c), join(bot_c)
        if all(c['text'] in 'oOºª°' for c in top_c): continue   # indicador ordinal (1º, 2ª)
        if not (re.fullmatch(r'[\w.,%+\-−]{1,8}', num) and re.fullmatch(r'[\w.,%+\-−]{1,8}', den)): continue
        if not num or not den: continue
        txt = f'{num}/{den}' if re.fullmatch(r'[\w.,%]+', num) and re.fullmatch(r'[\w.,%]+', den) else f'({num})/({den})'
        yc = (o['top'] + o['bottom']) / 2
        # caractere vizinho na linha principal, p/ alinhar
        cand = [c for c in chars if id(c) not in used and c not in top_c and c not in bot_c and c['top'] < yc < c['bottom'] and abs(_cx(c) - (o['x0'] + o['x1']) / 2) < 120]
        ref = min(cand, key=lambda c: abs(_cx(c) - (o['x0'] + o['x1']) / 2)) if cand else top_c[0]
        size = ref['size']; w = size * 0.52; x = (o['x0'] + o['x1']) / 2 - len(txt) * w / 2
        txt = ' ' + txt + ' '
        x = (o['x0'] + o['x1']) / 2 - len(txt) * w / 2
        nc = copy.copy(top_c[0]); nc.update(text=txt, x0=o['x0'], x1=o['x1'], top=ref['top'], bottom=ref['bottom'], size=size, width=o['x1'] - o['x0'], adv=o['x1'] - o['x0'])
        if 'doctop' in nc: nc['doctop'] = ref.get('doctop', nc['doctop'])
        new.append(nc)
        for c in top_c + bot_c: used.add(id(c))
        rm_bars.append(o); nfrac += 1
    # fracoes com digitos desenhados como curvas: OCR de cada metade
    import subprocess, tempfile, os
    def ocr_digits(bbox):
        try:
            im = p.crop(bbox).to_image(resolution=500).original.convert('L')
            w, h = im.size
            from PIL import Image
            canvas = Image.new('L', (w + 120, h + 120), 255); canvas.paste(im, (60, 60))
            fd, path = tempfile.mkstemp(suffix='.png'); os.close(fd); canvas.save(path)
            out = subprocess.run(['tesseract', path, '-', '--psm', '7', '-c', 'tessedit_char_whitelist=0123456789,.'], capture_output=True, text=True, timeout=30).stdout.strip()
            os.unlink(path)
            return re.sub(r'\s+', '', out)
        except Exception:
            return ''
    curves = objs.get('curve', [])
    for (k, o) in list(bars):
        if any(o is b for b in rm_bars): continue
        cx0, cx1 = o['x0'] - 3, o['x1'] + 3
        up = [c for c in curves if cx0 <= (c['x0'] + c['x1']) / 2 <= cx1 and o['top'] - 15 < c['bottom'] <= o['top'] + 1.5 and not infig(c)]
        dn = [c for c in curves if cx0 <= (c['x0'] + c['x1']) / 2 <= cx1 and o['bottom'] - 1.5 <= c['top'] < o['bottom'] + 15 and not infig(c)]
        if not up or not dn: continue
        def bb(cs): return (min(c['x0'] for c in cs) - 1, min(c['top'] for c in cs) - 1, max(c['x1'] for c in cs) + 1, max(c['bottom'] for c in cs) + 1)
        num, den = ocr_digits(bb(up)), ocr_digits(bb(dn))
        if not re.fullmatch(r'[\d.,]{1,6}', num) or not re.fullmatch(r'[\d.,]{1,6}', den): continue
        txt = ' ' + f'{num}/{den}' + ' '
        yc = (o['top'] + o['bottom']) / 2
        cand = [c for c in chars if id(c) not in used and c['top'] < yc < c['bottom'] and abs(_cx(c) - (o['x0'] + o['x1']) / 2) < 120]
        if not cand: continue
        ref = min(cand, key=lambda c: abs(_cx(c) - (o['x0'] + o['x1']) / 2))
        size = ref['size']; w = size * 0.52; x = (o['x0'] + o['x1']) / 2 - len(txt) * w / 2
        nc = copy.copy(ref); nc.update(text=txt, x0=o['x0'], x1=o['x1'], width=o['x1'] - o['x0'], adv=o['x1'] - o['x0'])
        new.append(nc)
        rm_bars.append(o); nfrac += 1
        for c in up + dn: c['__rm'] = True
    if curves: objs['curve'] = [c for c in curves if not c.get('__rm')]
    # expoentes / ordinais: so no corpo da pagina e colados a um caractere maior
    H = float(p.height)
    body = [c for c in chars if c['text'].strip() and 50 < c['top'] < H - 70]
    sizes = [c['size'] for c in body]
    med = statistics.median(sizes) if sizes else 10
    byline = {}
    for c in body: byline.setdefault(round(c['top'] / 3), []).append(c)
    for c in body:
        if id(c) in used or c['size'] >= med * 0.8 or infig(c): continue
        left = [o for o in body if o is not c and o['size'] >= med * 0.85 and 0 <= c['x0'] - o['x1'] < 2.5 and abs(o['top'] - c['top']) < o['size']]
        if not left: continue
        prev = max(left, key=lambda o: o['x1'])
        if c['text'].isdigit() and c['bottom'] < prev['bottom'] - 0.12 * prev['size']:
            c['text'] = c['text'].translate(SUP)
        elif c['text'] in ('o', 'a') and prev['text'].isdigit():
            c['text'] = 'º' if c['text'] == 'o' else 'ª'
    # lacunas (linhas de preencher) no meio do texto
    for k in ('line', 'rect'):
        for o in objs.get(k, []):
            w = o['x1'] - o['x0']; h = o['bottom'] - o['top']
            if not (15 <= w <= 150 and h <= 2.5) or infig(o) or any(o is b for b in rm_bars): continue
            above = [c for c in chars if id(c) not in used and c['text'].strip() and c['x1'] > o['x0'] + 1 and c['x0'] < o['x1'] - 1 and c['top'] - 1 <= o['top'] <= c['bottom'] + 1.5]
            if above: continue
            near = [c for c in chars if id(c) not in used and c['text'].strip() and c['top'] - 1 <= o['top'] <= c['bottom'] + 2 and (0 <= o['x0'] - c['x1'] < 14 or 0 <= c['x0'] - o['x1'] < 14)]
            if not near: continue
            ref = near[0]
            nc = copy.copy(ref); nc.update(text=' ______ ', x0=o['x0'], x1=o['x1'], top=ref['top'], bottom=ref['bottom'], width=w, adv=w)
            new.append(nc)
    if nfrac or True:
        objs['char'] = [c for c in chars if id(c) not in used] + new
        for k in ('line', 'rect'):
            if k in objs and rm_bars: objs[k] = [o for o in objs[k] if not any(o is b for b in rm_bars)]
    return nfrac
