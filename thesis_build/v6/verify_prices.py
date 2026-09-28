# -*- coding: utf-8 -*-
"""Re-derive the price tables (44, 46, 47, 48) straight from the .sav."""
import pyreadstat, pandas as pd, numpy as np, json, re
df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
ACT = {1.0:'Fisher',2.0:'Middleman',3.0:'Hotelier',4.0:'Exporter'}
SITE = {1.0:'Shimoni',2.0:'Majoreni',3.0:'Vanga',4.0:'Msambweni',5.0:'Other sites'}
df['_a']=df['actor'].map(ACT); df['_s']=df['bmu'].map(SITE)
G={'Large (Grade A)':'price_large_0_2','Medium (Grade B)':'price_medium_0_2','Small (Grade C)':'price_small_0_2'}
T={t['num']:t for t in json.load(open('v6/tables_final.json'))}
def f1(x): return f'{x:,.1f}'
err=0; ok=0

# ---- Table 44: descriptive statistics by actor and grade
cur=None
for row in T[45]['rows']:
    c0=str(row[0])
    if c0.startswith('__BLOCK__'): cur=G[c0[9:]]; continue
    a=c0.strip()
    if a not in ACT.values(): continue
    s=df.loc[df._a==a, cur].dropna()
    if len(s)==0: continue
    exp=[a,str(len(s)),f1(s.mean()),f1(s.std(ddof=1)) if len(s)>1 else '-',f1(s.median()),
         f'{f1(s.quantile(.25))}\u2013{f1(s.quantile(.75))}',f'{f1(s.min())}–{f1(s.max())}']
    got=[re.sub(r'\s+',' ',str(x)).strip() for x in row]
    for k,(x,y) in enumerate(zip(got,exp)):
        ok+=1
        if x.replace('–','-')!=y.replace('–','-'):
            err+=1; print(f'T45 {a} {cur} col{k}: doc={x!r} sav={y!r}')

# ---- Table 47: mean by actor x BMU x grade
cur=None
for row in T[48]['rows']:
    c0=str(row[0])
    if c0.startswith('__BLOCK__'): cur=G[c0[9:]]; continue
    site=c0.strip()
    for k,a in enumerate(['Fisher','Middleman','Hotelier','Exporter']):
        sub = df[df._a==a] if site=='All sites' else df[(df._a==a)&(df._s==site)]
        s=sub[cur].dropna()
        exp = '-' if len(s)==0 else f'{s.mean():,.1f} ({len(s)})'
        got=re.sub(r'\s+',' ',str(row[1+k])).strip()
        ok+=1
        if got!=exp: err+=1; print(f'T48 {site} {a} {cur}: doc={got!r} sav={exp!r}')

# ---- Table 48: fisher/middleman spread
cur=None
for row in T[49]['rows']:
    c0=str(row[0])
    if c0.startswith('__BLOCK__'): cur=G[c0[9:]]; continue
    site=c0.strip()
    fs=df[(df._a=='Fisher')&(df._s==site)][cur].dropna()
    ms=df[(df._a=='Middleman')&(df._s==site)][cur].dropna()
    if len(fs)==0: continue
    fm=fs.mean()
    exp=[site,f1(fm)]
    if len(ms)==0: exp+= ['-','-','-','-']
    else:
        mm=ms.mean()
        exp+=[f1(mm),f1(mm-fm),f'{(mm-fm)/fm*100:.1f}',f'{fm/mm*100:.1f}']
    got=[re.sub(r'\s+',' ',str(x)).strip() for x in row]
    for k,(x,y) in enumerate(zip(got,exp)):
        ok+=1
        if x!=y: err+=1; print(f'T49 {site} {cur} col{k}: doc={x!r} sav={y!r}')

# ---- Table 46: margins
means={g:{a:df.loc[df._a==a,c].dropna().mean() for a in ACT.values()} for g,c in G.items()}
chains=[('Large (Grade A) sold on to exporters','Large (Grade A)','Exporter'),
        ('Large (Grade A) sold on to hoteliers','Large (Grade A)','Hotelier'),
        ('Medium (Grade B) sold on to exporters','Medium (Grade B)','Exporter')]
cur=None
for row in T[47]['rows']:
    c0=str(row[0])
    if c0.startswith('__BLOCK__'):
        cur=next((c for c in chains if c[0]==c0[9:]), None); continue
    if cur is None: continue
    node=c0.split(' (')[0].strip()
    g, end = cur[1], cur[2]
    final=means[g][end]
    if node=='Fisher': price, margin = means[g]['Fisher'], means[g]['Fisher']; mpct='-'
    elif node=='Middleman':
        price=means[g]['Middleman']; margin=price-means[g]['Fisher']
        mpct=f'{margin/means[g]["Fisher"]*100:.1f}'
    elif node==end:
        price=final; margin=final-means[g]['Middleman']
        mpct=f'{margin/means[g]["Fisher"]*100:.1f}'
    else:
        continue
    exp=[f1(price), f1(margin), mpct, f'{margin/final*100:.1f}']
    got=[re.sub(r'\s+',' ',str(x)).strip().replace('\u2014','-') for x in row[1:]]
    for k,(x,y) in enumerate(zip(got,exp)):
        ok+=1
        if x!=y: err+=1; print(f'T47 {cur[0]} / {node} col{k}: doc={x!r} sav={y!r}')
print(f'\nprice/margin figures re-derived: {ok}   mismatches: {err}')
