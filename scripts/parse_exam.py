"""Parser de questoes a partir do fluxo gerado por build_stream.py.
Saida: lista de dicts {num, disc, base, enun, alts{A..E}, visual(bool), page}
"""
import re, sys, os, json, glob, collections

FOOT_RES = [re.compile(p, re.I) for p in [
    r'^Confidencial até', r'^\d{1,2}\s+[a-z]{3,6}\d{3,4}/\d{3}', r'^[a-z]{3,6}\d{3,4}/\d{3}.*\d{1,2}$', r'^[a-z]{3,6}\d{3,4}/\d{3}\b', r'^www\.ConcursoPM', r'^https?://www\.concursopm',
    r'^Canal Concurso PM', r'^YouTube\.com/CanalConcursoPM', r'^@ConcursoPMoficial', r'^vers.o ?\d+$',
    r'^\d{6}$', r'^r ?a ?s ?c ?u ?n ?h ?o$', r'^polícia militar do estado de são paulo$',
    r'^SECRETARIA DA SEGURANÇA', r'^FGV CONHECIMENTO', r'^\s*$',
]]

DISC_MAP = {
    'língua portuguesa': 'Língua Portuguesa', 'língua portuguesa e interpretação de texto': 'Língua Portuguesa',
    'matemática': 'Matemática', 'conhecimentos gerais': 'Conhecimentos Gerais', 'conhecimentos específicos': 'Conhecimentos Específicos',
    'história geral': 'História Geral', 'história do brasil': 'História do Brasil', 'geografia geral': 'Geografia Geral',
    'geografia do brasil': 'Geografia do Brasil', 'atualidades': 'Atualidades',
    'noções básicas de informática': 'Noções Básicas de Informática', 'noções de informática': 'Noções Básicas de Informática',
    'informática': 'Noções Básicas de Informática', 'noções de administração pública': 'Noções de Administração Pública',
    'noções de direito': 'Noções de Direito', 'direitos humanos': 'Direitos Humanos',
}

def letters_sig(t):
    return ''.join(sorted(c for c in t.lower() if c.isalpha()))
HEAD_SIGS = {}
for _k in list(DISC_MAP):
    HEAD_SIGS[letters_sig(_k)] = _k

INSTR_RE = re.compile(r'quest[õo]es?\s+(?:de\s+)?(?:n[úu]meros?\s+)?0?(\d{1,2})\s*(?:a|e|à|ao|até|-|–)\s*0?(\d{1,2})', re.I)
INSTR1_RE = re.compile(r'quest[ãa]o\s+(?:de\s+)?n[úu]mero\s+0?(\d{1,2})\b', re.I)
VIS_INSTR = re.compile(r'\b(tira|tirinha|charge|cartum|cartaz|figura|imagem|mapa|infogr[áa]fico|ilustra[çc][ãa]o|fotografia|pintura|gr[áa]fico|anúncio|propaganda|esquema)s?\b', re.I)
VIS_ENUN = re.compile(r'\b(observ\w+|analis\w+|consider\w+|leia|veja)\b.{0,50}\b(figura|imagem|gráfico|mapa|charge|tira|tirinha|infográfico|cartaz|ilustração|esquema)\b', re.I)
Q_START = re.compile(r'^(\d{1,2})\.\s+(\S.*)$')
ALT_START = re.compile(r'^\(([A-E])\)\s*(.*)$')

class Vocab:
    def __init__(self):
        self.c = collections.Counter()
    def feed(self, lines):
        for ln in lines:
            t = ln.replace('\x01', '').replace('\x02', '')
            if t.startswith('@@'):
                continue
            if t.rstrip().endswith('-'):
                t = t.rstrip()[:-1]
            for w in re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*", t):
                self.c[w.lower()] += 1

VOCAB = Vocab()

def merge(cur, t):
    """junta duas linhas tratando hifenizacao de fim de linha"""
    if cur.endswith('-') and len(cur) > 1 and cur[-2].isalpha():
        m1 = re.search(r'([A-Za-zÀ-ÿ]+)-$', cur)
        m2 = re.match(r'^-?([A-Za-zÀ-ÿ]+)', t)
        if m1 and m2:
            pre, suf = m1.group(1), m2.group(1)
            if t.startswith('-'):
                return cur + t.lstrip('-').lstrip() if False else cur[:-1] + '-' + t[1:]
            joined = (pre + suf).lower(); hyph = (pre + '-' + suf).lower()
            if VOCAB.c.get(hyph, 0) > VOCAB.c.get(joined, 0) or suf[0].isupper():
                return cur + t
            return cur[:-1] + t
    return cur + ' ' + t

def join(lines, para=True):
    paras, cur, prev_short = [], '', False
    for (t, ind, short) in lines:
        t = t.strip()
        if not t:
            continue
        if cur and para and (ind or prev_short):
            paras.append(cur); cur = t
        elif cur:
            cur = merge(cur, t)
        else:
            cur = t
        prev_short = short
    if cur:
        paras.append(cur)
    out = '\n'.join(paras)
    return fix_spaces(out)

SINGLE_OK = set('aeoàáâãéêíóôõúüç')
def fix_spaces(s):
    def rep(m):
        a, b = m.group(1), m.group(2)
        j = (a + b).lower()
        if VOCAB.c.get(j, 0) >= 2 and VOCAB.c.get(a.lower(), 0) < 5:
            return a + b
        return m.group(0)
    return re.sub(r'(?<![\w(])([b-df-hj-np-tv-zB-DF-HJ-NP-TV-Z])\s([a-zà-ú]{3,})', rep, s)

def split_flags(line):
    ind = line.startswith('\x01'); short = line.endswith('\x02')
    return line.replace('\x01', '').replace('\x02', '').strip(), ind, short

def fix_smallcaps(lines):
    """junta fragmentos de titulos em versalete ('H G' + 'istória eral') num marcador de disciplina"""
    out = []; i = 0
    while i < len(lines):
        a = lines[i].replace('\x01', '').replace('\x02', '').strip()
        if i + 1 < len(lines) and re.fullmatch(r'(?:[A-ZÀ-Ú]\s?){1,4}', a) and not lines[i + 1].startswith('@@'):
            b = lines[i + 1].replace('\x01', '').replace('\x02', '').strip()
            sig = letters_sig(a + b)
            if len(b) < 40 and sig in HEAD_SIGS:
                out.append('@@H:' + HEAD_SIGS[sig]); i += 2; continue
        out.append(lines[i]); i += 1
    return out

def parse(stream_lines, maxq=60):
    stream_lines = fix_smallcaps(stream_lines)
    expected = 1
    qs = []; groups = []
    cur = None; mode = 'pre'; disc = None; group_name = None
    page = 0; last_was_img = False
    i = 0
    n = len(stream_lines)
    def finish():
        nonlocal cur
        if cur is not None:
            qs.append(cur); cur = None
    while i < n:
        raw = stream_lines[i]; i += 1
        if raw.startswith('@@PAGE'):
            page = int(raw.split()[1]); continue
        if raw.startswith('@@H:'):
            key = raw[4:]
            if key == 'redação':
                if expected > 40:
                    finish(); break
                continue
            name = DISC_MAP.get(key)
            if name:
                disc = name
            continue
        if raw.startswith('@@IMG'):
            fg = raw[6:].strip() if raw[6:].startswith('fig:') else None
            if mode in ('enun', 'alt') and cur is not None:
                cur['img'] = True
                if fg: cur.setdefault('afigs' if mode == 'alt' else 'figs', []).append(fg[4:])
            elif mode == 'block' and groups:
                groups[-1]['img'] = True
                if fg: groups[-1].setdefault('figs', []).append(fg[4:])
            last_was_img = True
            continue
        text, ind, short = split_flags(raw)
        text = re.sub(r'\s*\d{0,2}\s*Confidencial até o momento da aplicação\.?(?:\s*\d{1,2}\s*$)?', '', text).strip()
        if not text or any(r.search(text) for r in FOOT_RES):
            continue
        was_img = last_was_img; last_was_img = False
        hk = re.sub(r'\s+', ' ', text.lower()).strip(' .')
        if hk in DISC_MAP and len(text) < 50:
            disc = DISC_MAP[hk]
            continue
        if len(text) < 40 and not re.search(r'[.,;:?!()\d]', text):
            sig = letters_sig(text)
            if sig in HEAD_SIGS:
                disc = DISC_MAP[HEAD_SIGS[sig]]
                continue
        # fim da prova objetiva
        if expected > maxq - 0 and re.match(r'(?i)^(proposta de )?reda[çc][ãa]o$', text):
            finish(); break
        # instrucao de grupo de texto
        cand = text
        mm = INSTR_RE.search(cand); m1 = INSTR1_RE.search(cand)
        if not (mm or m1) and re.search(r'(?i)(para responder|responder às|responder as|quest[õo]es? de n)', cand) and text[0].isupper() and i < n:
            nxt, _, _ = split_flags(stream_lines[i]) if not stream_lines[i].startswith('@@') else ('', 0, 0)
            cand2 = cand + ' ' + nxt
            mm = INSTR_RE.search(cand2); m1 = INSTR1_RE.search(cand2)
            if mm or m1:
                i += 1; cand = cand2
        if (mm or m1) and text[0].isupper() and len(cand) < 220 and re.search(r'(?i)\b(leia|observe|considere|analise|para|com base|os? texto|a charge|o gráfico|a tira|as?)\b', cand):
            finish() if mode in ('enun', 'alt') else None
            if mm:
                lo, hi = int(mm.group(1)), int(mm.group(2))
                if hi < lo:  # ex.: 'números 05 e 6'
                    hi = lo
            else:
                lo = hi = int(m1.group(1))
            groups.append({'lo': lo, 'hi': hi, 'instr': cand, 'lines': [], 'img': False, 'credit': None,
                           'visual': bool(VIS_INSTR.search(cand))})
            mode = 'block'
            continue
        # inicio de questao
        qm = Q_START.match(text)
        if qm and int(qm.group(1)) == expected:
            finish()
            cur = {'num': expected, 'disc': disc, 'enun': [(qm.group(2), ind, short)], 'alts': collections.OrderedDict(),
                   'img': False, 'page': page, 'cur_alt': None}
            expected += 1; mode = 'enun'
            continue
        am = ALT_START.match(text)
        if am and cur is not None and mode in ('enun', 'alt'):
            letter = am.group(1)
            nextl = 'ABCDE'[len(cur['alts'])] if len(cur['alts']) < 5 else None
            if letter == nextl:
                cur['alts'][letter] = [(am.group(2), ind, short)]
                cur['cur_alt'] = letter; mode = 'alt'
                continue
        if mode == 'enun' and cur is not None:
            cur['enun'].append((text, ind, short))
        elif mode == 'alt' and cur is not None:
            cur['alts'][cur['cur_alt']].append((text, ind, short))
        elif mode == 'block' and groups:
            g = groups[-1]
            if was_img and re.match(r'^\(.*\)$', text):
                g['credit'] = text
            else:
                g['lines'].append((text, ind, short))
    finish()
    # monta saida
    out = []
    for q in qs:
        grp = None
        for g in groups:
            if g['lo'] <= q['num'] <= g['hi']:
                grp = g
        base = join(grp['lines']) if grp and grp['lines'] else ''
        enun = join(q['enun'], para=False)
        enun_para = join(q['enun'], para=True)
        # listas de assercoes (I., II., ...) em linhas proprias
        enun_txt = re.sub(r'\s+(?=(?:I{1,3}|IV|V)\.\s)', '\n', enun)
        alts = {k: join(v, para=False) for k, v in q['alts'].items()}
        visual = bool(q['img'] or (grp and (grp['img'] or grp['visual'])) or VIS_ENUN.search(enun))
        out.append({'num': q['num'], 'disc': q['disc'], 'base': base, 'enun': enun_txt, 'alts': alts,
                    'visual': visual, 'page': q['page'], 'group': (grp['lo'], grp['hi']) if grp else None,
                    'credit': grp['credit'] if grp else None,
                    'figs': list(grp.get('figs', [])) if grp else [], 'qfigs': list(q.get('figs', [])), 'afigs': list(q.get('afigs', []))})
    return out

def load_stream(path):
    return open(path, encoding='utf8').read().split('\n')

def build_vocab(stream_dir):
    for f in glob.glob(os.path.join(stream_dir, '*.txt')):
        VOCAB.feed(load_stream(f))

if __name__ == '__main__':
    sd = sys.argv[1]
    build_vocab(sd)
    for f in sorted(glob.glob(os.path.join(sd, '*.txt'))):
        name = os.path.basename(f)[:-4]
        qs = parse(load_stream(f))
        full = sum(1 for q in qs if len(q['alts']) == 5)
        segs = []
        for q in qs:
            if not segs or segs[-1][0] != q['disc']:
                segs.append([q['disc'], q['num'], q['num']])
            else:
                segs[-1][2] = q['num']
        print(f'{name}: {len(qs)} questoes, {full} com 5 alt, visuais={sum(q["visual"] for q in qs)}')
        print('    ', '; '.join(f'{s[0]} {s[1]}-{s[2]}' for s in segs))
