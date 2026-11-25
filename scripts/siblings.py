import sys, re, glob, os, collections, itertools
sys.path.insert(0,'scripts')
import parse_exam as P
P.build_vocab('work/stream')
def fp(s):
    return re.sub(r'[^a-z0-9]','',s.lower())[:70]
data={}
for f in sorted(glob.glob('work/stream/*.txt')):
    n=os.path.basename(f)[:-4]
    qs=P.parse(P.load_stream(f))
    data[n]={fp(q['enun']+' '+q['alts'].get('A','')[:20]) for q in qs if q['enun']}
names=list(data)
print('provas:',len(names))
for a,b in itertools.combinations(names,2):
    inter=len(data[a]&data[b]); m=min(len(data[a]),len(data[b]))
    if m and inter/m>0.3: print(f'{a[-24:]:>26} ~ {b[-24:]:<26} {inter}/{m}')
