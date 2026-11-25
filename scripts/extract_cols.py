import sys, os, glob, pdfplumber
src = sys.argv[1]; out = sys.argv[2]
os.makedirs(out, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, '*prova*.pdf'))):
    name = os.path.basename(f)[:-4]
    lines = []
    with pdfplumber.open(f) as pdf:
        for i, p in enumerate(pdf.pages, 1):
            W, H = p.width, p.height
            lines.append(f'=== PAGE {i} ({W:.0f}x{H:.0f}) imgs={len(p.images)}')
            body = p.crop((0, 0, W, H))
            for tag, box in (('L', (0, 0, W/2, H)), ('R', (W/2, 0, W, H))):
                try:
                    t = p.crop(box).extract_text(x_tolerance=1.5, y_tolerance=2) or ''
                except Exception as e:
                    t = f'[erro {e}]'
                lines.append(f'--- {tag} ---')
                lines.append(t)
    open(os.path.join(out, name + '.txt'), 'w', encoding='utf8').write('\n'.join(lines))
    print('ok', name)
