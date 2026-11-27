import json, re, os, shutil, sys
sys.path.insert(0,'scripts')
raw = json.load(open('work/dataset_raw.json'))
FIGDIR = {'pmes1703':'2017_02_prova_soldado_dp2','pmes1803':'2018_02_prova_soldado_dp2','pmes1902':'2019_02_prova_soldado_dp2','pmes2203':'2023_01_prova_soldado_pmes2203','pmes2502':'2025_02_prova_soldado_pmes2502','pmes2601':'2026_01_prova_aluno_soldado','pmes2104':'sem_ano_prova_view_7','pmes1903':'sem_ano_prova_view_8','pmes1901':'sem_ano_prova_view_10','pmes1602':'sem_ano_prova_view_14','pmes1501':'sem_ano_prova_view_15','pmes1201':'sem_ano_prova_view_20'}
out_dir = 'site/img'; shutil.rmtree(out_dir, ignore_errors=True); os.makedirs(out_dir)
QI = {e: json.load(open(f'work/qi/{e}/q.json')) for e in FIGDIR}
used = {}
def pub(src, dst):
    if dst not in used:
        from PIL import Image
        im = Image.open(src).convert('RGB')
        im.save(os.path.join(out_dir, dst), optimize=True)
        used[dst] = 1
    return 'img/' + dst
out = []; stats = {}
for q in raw:
    a = q['alts']; e = q['exam']
    qi = QI[e].get(str(q['num']))
    incomplete = len(a) < 5 or any(not v.strip() for v in a.values())
    qfg = (qi or {}).get('figs', {'stem': [], 'alt': []})
    hasfig = bool(q.get('figs') or qfg['stem'] or qfg['alt'])
    nofig = (bool(q.get('visual')) or bool(re.search(r'(?i)(\b(observe|analise|veja|leia|considere|utilize|examine)\b[^.]{0,60}\b(tirinhas?|tiras?|quadrinhos|charge|figura|imagem|gr[áa]fico|tabela|mapa|planilha|cartaz|infogr[áa]fico|esquema|fotografia|tela)\b|\b(tirinhas?|tiras?|charge|figura|imagem|gr[áa]fico|tabela|mapa|planilha|cartaz|infogr[áa]fico|tela)\b[^.]{0,25}\b(a seguir|abaixo|acima|apresentad[ao]|mostra|ilustra)|\b(na|da|pela|dessa|desta) (tirinha|tira|charge|figura|imagem|planilha|tabela|tela)\b|\bgr[áa]fico apresenta)', q['enun'][:260]))) and not hasfig
    stem_img = bool(qi and len(qi['alts']) == 5 and (nofig or (qi.get('vstem') and not (hasfig or re.search(r'\d\s*/\s*\d', q['enun'])))))
    alts_img = bool(qi and len(qi['alts']) == 5 and (incomplete or (qi.get('valt') and not (hasfig or all(re.search(r'\d', v) for v in a.values()) and any(re.search(r'\d\s*/\s*\d', v) for v in a.values())))))
    mode = ('stem+alts' if stem_img and alts_img else 'stem' if stem_img else 'alts' if alts_img else None)
    if incomplete and not alts_img:
        continue
    disc = q['disc'] or 'Língua Portuguesa'
    disc = {'Noções Básicas de Informática': 'Noções de Informática'}.get(disc, disc)
    d = {'id': f"{e}-{q['num']:02d}", 'exam': e, 'numero': q['num'], 'codigo': f"{e.upper()}-{q['num']:02d}",
         'materia': disc, 'banca': 'VUNESP', 'orgao': 'PMESP',
         'cargo': 'Aluno-Soldado PM' if e == 'pmes2601' else 'Soldado PM de 2ª Classe',
         'ano': q['ano'], 'prova': q['rot'], 'enunciado': q['enun'], 'alternativas': a,
         'gabarito': q['gab'] if q['gab'] != '*' else None, 'anulada': q['gab'] == '*'}
    if q['base']: d['texto'] = q['base']
    if q.get('credit'): d['credito'] = q['credit']
    gf = [pub(f'work/figs/{n}', f'{e}_{os.path.basename(n)}') for n in q.get('figs', [])]
    if gf: d['figuras'] = gf
    qf = [pub(f'work/figs/{n}', f'{e}_{os.path.basename(n)}') for n in qfg['stem']]
    if not alts_img:
        qf += [pub(f'work/figs/{n}', f'{e}_{os.path.basename(n)}') for n in qfg['alt']]
    if qf and not stem_img: d['figuras_q'] = qf
    if mode:
        d['imgq'] = {'f': pub(f'work/qi/{e}/{qi["f"]}', f'{e}_{qi["f"]}'), 'w': qi['w'], 'h': qi['h'], 'alts': qi['alts'], 'stem': stem_img, 'altimg': alts_img}
    stats[mode or 'txt'] = stats.get(mode or 'txt', 0) + 1
    out.append(d)
LP,MT,HG,HB,GG,GB,AT,IN,AD = 'Língua Portuguesa','Matemática','História Geral','História do Brasil','Geografia Geral','Geografia do Brasil','Atualidades','Noções de Informática','Noções de Administração Pública'
S60 = [(1,LP),(21,MT),(36,HG),(38,HB),(42,GG),(44,GB),(48,AT),(51,IN),(56,AD)]
S50 = [(1,LP),(19,MT),(31,HG),(33,HB),(35,GG),(37,GB),(39,AT),(41,IN),(46,AD)]
STARTS = {'pmes1803':[(1,LP),(19,MT),(31,HG),(33,HB),(37,GG),(39,GB),(43,AT),(45,IN),(53,AD)],
 'pmes1901':[(1,LP),(21,MT),(35,HG),(37,HB),(41,GG),(43,GB),(47,AT),(49,IN),(55,AD)],
 'pmes1201':[(1,LP),(21,MT),(36,HG),(38,HB),(41,GG),(43,GB),(46,AT)],
 'pmes1501':S50,'pmes1703':S50,'pmes1602':S50,
 'pmes2601':[(1,LP),(21,MT),(36,HG),(39,HB),(42,GG),(45,GB),(48,AT),(51,IN),(56,AD)]}
for d in out:
    tb = STARTS.get(d['exam'], S60); m = tb[0][1]
    for st, nm in tb:
        if d['numero'] >= st: m = nm
    d['materia'] = m
def clean(t, exam):
    if not t: return t
    t = re.sub(r'<([^<>=]{1,400}?)=', lambda m: '“' + m.group(1).strip() + '”', t)
    if exam in ('pmes1903', 'pmes1901'):
        t = re.sub(r'\s&(?=\s|$)', ' …', t); t = re.sub(r'(?<=\w)&', '…', t)
    if exam == 'pmes1903':
        t = re.sub(r'(?<=[A-Za-zÀ-ú,.;)”]) 3 (?=[A-Za-zÀ-ú“(])', ' – ', t)
    t = re.sub(r'\b(\d{1,2})([oa])\b(?=\s+(?:parágrafo|verso|estrofe|trecho|período|capítulo|semestre|dia|ano|lugar|andar|turno|mês|colocad|classe|Classe|item|artigo|Batalhão|Regimento|Região))', lambda m: m.group(1) + ('º' if m.group(2) == 'o' else 'ª'), t)
    return t
for d in out:
    for k in ('enunciado', 'texto', 'credito'):
        if d.get(k): d[k] = clean(d[k], d['exam'])
    if d.get('alternativas'): d['alternativas'] = {k: clean(v, d['exam']) for k, v in d['alternativas'].items()}
import overrides as OV
from PIL import Image
for d in out:
    o = OV.O.get(d['id'])
    if not o: continue
    blocos = []; crops = []; n = 0
    qimg = Image.open(f"work/qi/{d['exam']}/q{d['numero']:02d}.png") if any(x[0] == 'c' for x in o['b']) else None
    figs0 = list(d.get('figuras_q') or [])
    for x in o['b']:
        if x[0] == 't': blocos.append({'t': x[1]})
        elif x[0] == 'f': blocos.append({'i': figs0[x[1]]}); crops.append(figs0[x[1]])
        elif x[0] == 'p':
            import pdfplumber
            n += 1; nm = f"{d['id']}_b{n}.png"
            pg = pdfplumber.open(f"provas_zip/{x[1]}.pdf").pages[x[2] - 1]
            pg.crop((x[3], x[4], x[5], x[6])).to_image(resolution=230).save(os.path.join(out_dir, nm))
            blocos.append({'i': 'img/' + nm}); crops.append('img/' + nm)
        else:
            n += 1; nm = f"{d['id']}_b{n}.png"; im = qimg.crop((x[3], x[1], min(x[4], qimg.width), min(x[2], qimg.height))); im.save(os.path.join(out_dir, nm)); used.add(nm) if isinstance(used, set) else None
            blocos.append({'i': 'img/' + nm}); crops.append('img/' + nm)
    d['blocos'] = blocos; d['enunciado'] = '\n'.join(x['t'] for x in blocos if 't' in x)
    if crops: d['figuras_q'] = crops
    else: d.pop('figuras_q', None)
    if o.get('a'): d['alternativas'] = o['a']
    if o.get('altimg') and d.get('imgq'): d['imgq']['stem'] = False; d['imgq']['altimg'] = True
    else: d.pop('imgq', None)
json.dump(out, open('site/questoes.json', 'w'), ensure_ascii=False)
tot = sum(os.path.getsize(os.path.join(out_dir, f)) for f in os.listdir(out_dir))
print(len(out), stats, 'arquivos', len(used), 'MB', round(tot / 1e6, 1))
