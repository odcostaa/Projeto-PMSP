import sys, re, os
sys.path.insert(0,'scripts')
import parse_exam as P, gabaritos as G
P.build_vocab('work/stream')
def fp(q): return re.sub(r'[^a-z0-9]','',(q['enun']+' '+q['alts'].get('A','')[:20]).lower())[:70]
def prova(n): return P.parse(P.load_stream(f'work/stream/{n}.txt'))
def gab(n):
    return G.parse_gab(G.pdftext(f'provas_zip/{n}.pdf'))
def alt_text(q,l): return re.sub(r'\W','',q['alts'].get(l,'').lower())
def compare(pa, ga, va, pb, gb, vb):
    A=prova(pa); B=prova(pb)
    fb={fp(q):q for q in B}
    ga_=gab(ga)[va]; gb_=gab(gb)[vb]
    ok=bad=0; badl=[]
    for q in A:
        o=fb.get(fp(q))
        if not o: continue
        la=ga_.get(q['num']); lb=gb_.get(o['num'])
        if la in 'ABCDE' and lb in 'ABCDE' and la and lb:
            if alt_text(q,la)==alt_text(o,lb): ok+=1
            else: bad+=1; badl.append((q['num'],o['num'],la,lb))
    return ok,bad,badl[:6]
tests=[
 ('2019_02_prova_soldado_dp2','2019_02_gabarito_soldado_dp2','1','sem_ano_prova_view_9','sem_ano_gabarito_view_9','4'),
 ('2017_02_prova_soldado_dp2','2017_02_gabarito_soldado_dp2','2','sem_ano_prova_view_13','sem_ano_gabarito_view_13','4'),
 ('2023_01_prova_soldado_pmes2203','2023_01_gabarito_soldado_pmes2203','1','sem_ano_prova_view_5','sem_ano_gabarito_view_5','1'),
]
for v in '1234':
    tests.append(('2018_02_prova_soldado_dp2','2018_02_gabarito_soldado_dp2',v,'sem_ano_prova_view_11','sem_ano_gabarito_view_11','1'))
for t in tests:
    print(t[0][:24],'v',t[2],'<->',t[3][-12:],'v',t[5],':',compare(*t))
