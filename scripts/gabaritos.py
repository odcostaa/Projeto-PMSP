"""Le os gabaritos (texto) e devolve {versao: {num: letra|'*'}}."""
import re, glob, os, sys, json, subprocess

def pdftext(path):
    return subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout

PAIR = re.compile(r'(?<![\d])(\d{1,2})\s*[-–=.]\s*([A-E*])(?![A-Za-z])')

def parse_gab(txt):
    # separa por 'VERSÃO n' / 'TIPO n'
    parts = re.split(r'(?im)^\s*(?:vers[aã]o|tipo|caderno)\s*[:\-]?\s*(\d)\b.*$', txt)
    out = {}
    if len(parts) == 1:
        out['?'] = dict((int(a), b) for a, b in PAIR.findall(txt))
        return out
    # parts = [pre, v1, text1, v2, text2 ...]
    for k in range(1, len(parts), 2):
        out[parts[k]] = dict((int(a), b) for a, b in PAIR.findall(parts[k + 1]))
    return out

if __name__ == '__main__':
    for f in sorted(glob.glob(os.path.join(sys.argv[1], '*gabarito*.pdf'))):
        txt = pdftext(f)
        g = parse_gab(txt)
        info = {v: (len(d), sum(1 for x in d.values() if x == '*')) for v, d in g.items()}
        print(os.path.basename(f)[:-4], info)
