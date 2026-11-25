import pdfplumber,re,sys,json
KEY=[('lingua','língua portuguesa'),('matem','matemática'),('hist.* geral','história geral'),('historia do bra|história do bra|hist.ria do brasil','história do brasil'),('geografia geral|geogra.*geral','geografia geral'),('geografia do bra|geogra.*do bra','geografia do brasil'),('atualidades','atualidades'),('inform','noções de informática'),('administra','noções de administração pública')]
ex={'1803':'2018_02_prova_soldado_dp2','1903':'sem_ano_prova_view_8','2203':'2023_01_prova_soldado_pmes2203','2502':'2025_02_prova_soldado_pmes2502','1501':'sem_ano_prova_view_15','1703':'2017_02_prova_soldado_dp2','1602':'sem_ano_prova_view_14','1201':'sem_ano_prova_view_20','1901':'sem_ano_prova_view_10','1902':'2019_02_prova_soldado_dp2','2104':'sem_ano_prova_view_7','2601':'2026_01_prova_aluno_soldado'}
res={}
for k,n in ex.items():
    pdf=pdfplumber.open(f'provas_zip/{n}.pdf'); hits=[]
    for pi,p in enumerate(pdf.pages,1):
        W=p.width; mid=W/2
        for ci,(a,b) in enumerate([(0,mid),(mid,W)]):
            for ln in p.crop((a,0,b,p.height)).extract_text_lines(x_tolerance=3):
                t=ln['text'].lower()
                if len(t)>45 or ln['top']<20: continue
                for rx,name in KEY:
                    if re.search(rx,t) and not re.search(r'\d',t):
                        # proxima questao abaixo na mesma coluna
                        nq=None
                        for l2 in p.crop((a,ln['top']-2,b,p.height)).extract_text_lines(x_tolerance=3):
                            m=re.match(r'0?(\d{1,2})\.\s',l2['text'])
                            if m: nq=int(m.group(1)); break
                        hits.append((pi,ci,round(ln['top']),name,nq,ln['text'][:30]))
    res[k]=hits; print('==',k)
    for h in hits: print('  ',h)
