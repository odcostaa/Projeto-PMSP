import sys, re, json, os
sys.path.insert(0,'scripts')
import parse_exam as P, gabaritos as G
P.build_vocab('work/stream')
# (id, prova, gabarito, versao, ano, rotulo)
EX = [
 ('pmes1703','2017_02_prova_soldado_dp2','2017_02_gabarito_soldado_dp2','2',2017,'PMESP 2017 – Soldado PM 2ª Classe (PMES1703)'),
 ('pmes1803','2018_02_prova_soldado_dp2','2018_02_gabarito_soldado_dp2','1',2018,'PMESP 2018 – Soldado PM 2ª Classe (PMES1803)'),
 ('pmes1902','2019_02_prova_soldado_dp2','2019_02_gabarito_soldado_dp2','1',2019,'PMESP 2019 – Soldado PM 2ª Classe (PMES1902)'),
 ('pmes2203','2023_01_prova_soldado_pmes2203','2023_01_gabarito_soldado_pmes2203','1',2023,'PMESP 2023 – Soldado PM 2ª Classe (PMES2203)'),
 ('pmes2502','2025_02_prova_soldado_pmes2502','2025_02_gabarito_soldado_pmes2502','1',2025,'PMESP 2025 – Soldado PM 2ª Classe (PMES2502)'),
 ('pmes2601','2026_01_prova_aluno_soldado','2026_01_gabarito_aluno_soldado','1',2026,'PMESP 2026 – Aluno-Soldado (PMES2601)'),
 ('pmes2104','sem_ano_prova_view_7','sem_ano_gabarito_view_7','2',2021,'PMESP 2021 – Soldado PM 2ª Classe (PMES2104)'),
 ('pmes1903','sem_ano_prova_view_8','sem_ano_gabarito_view_8','4',2019,'PMESP 2019 – Soldado PM 2ª Classe (PMES1903)'),
 ('pmes1901','sem_ano_prova_view_10','sem_ano_gabarito_view_10','1',2019,'PMESP 2019 – Soldado PM 2ª Classe (PMES1901)'),
 ('pmes1602','sem_ano_prova_view_14','sem_ano_gabarito_view_14','?',2016,'PMESP 2016 – Soldado PM 2ª Classe (PMES1602)'),
 ('pmes1501','sem_ano_prova_view_15','sem_ano_gabarito_view_15','?',2015,'PMESP 2015 – Soldado PM 2ª Classe (PMES1501)'),
 ('pmes1201','sem_ano_prova_view_20','sem_ano_gabarito_view_20','?',2012,'PMESP 2012 – Soldado PM 2ª Classe (PMES1201)'),
]
def garble(q):
    t=' '.join([q['enun']]+list(q['alts'].values()))
    return len(re.findall(r'[^\w\s.,;:!?()\-–—"“”‘’\'/%$°ºª§…«»+=*<>→\[\]]',t))
out=[];rep=[]
for eid,pn,gn,gv,ano,rot in EX:
    qs=P.parse(P.load_stream(f'work/stream/{pn}.txt'))
    gs=G.parse_gab(G.pdftext(f'provas_zip/{gn}.pdf'))[gv]
    nq=len(qs); ng=len(gs)
    bad=0;anul=0;noalt=0;gar=0
    for q in qs:
        L=gs.get(q['num'])
        q['exam']=eid;q['ano']=ano;q['rot']=rot;q['gab']=L
        if L is None: bad+=1
        if L=='*': anul+=1
        if len(q['alts'])<5 or any(not v.strip() for v in q['alts'].values()): noalt+=1
        gar+=garble(q)>3
        out.append(q)
    rep.append((eid,nq,ng,bad,anul,noalt,gar))
    print(eid,'q',nq,'gab',ng,'semgab',bad,'anuladas',anul,'alt-incompleta',noalt,'ruido',gar)
json.dump(out,open('work/dataset_raw.json','w'),ensure_ascii=False)
