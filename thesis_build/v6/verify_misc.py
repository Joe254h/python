# -*- coding: utf-8 -*-
"""Re-derive Table 1 (sample), Table 11 (income and age) and Table 60 (the
significant associations) straight from the .sav."""
import pyreadstat, pandas as pd, numpy as np, json, re
df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
ACT={1.0:'Fisher',2.0:'Middleman',3.0:'Hotelier',4.0:'Exporter'}
SITE={1.0:'Shimoni',2.0:'Majoreni',3.0:'Vanga',4.0:'Msambweni',5.0:'Other sites'}
SITES=['Shimoni','Majoreni','Vanga','Msambweni','Other sites']
df['_a']=df['actor'].map(ACT); df['_s']=df['bmu'].map(SITE)
T={t['num']:t for t in json.load(open('v6/tables_final.json'))}
def f1(x): return f'{x:,.1f}'
err=ok=0

# ---- Table 1
ct=pd.crosstab(df._a, df._s)
for row in T[2]['rows']:
    a=str(row[0]).strip()
    def cp(c, tot): return f'{c} ({round(100.0*c/tot,1):.1f}%)'
    if a=='Total':
        cs=[int(df._s.eq(s).sum()) for s in SITES]; tot=len(df)
    elif a in ACT.values():
        cs=[int(ct.loc[a,s]) if s in ct.columns else 0 for s in SITES]; tot=int((df._a==a).sum())
    else: continue
    exp=[cp(c,tot) for c in cs]+[cp(tot,tot)]
    got=[str(x).strip() for x in row[1:]]
    for k,(x,y) in enumerate(zip(got,exp)):
        ok+=1
        if x!=y: err+=1; print(f'T2 {a} {SITES[k] if k<5 else "Total"}: doc={x!r} sav={y!r}')

# ---- Table 11: income and age
VARS={'Reported monthly mud crab income (KSh)':'income_ksh_0_1',
      'Age of respondents (years)':'age_0_1'}
cur=None
for row in T[10]['rows']:
    c0=str(row[0])
    if c0.startswith('__BLOCK__'):
        cur=VARS.get(c0[9:]); continue
    a=c0.strip()
    if cur is None or a not in ACT.values(): continue
    s=df.loc[df._a==a, cur].dropna()
    if len(s)==0: continue
    exp=[a,str(len(s)),f1(s.mean()),f1(s.std(ddof=1)) if len(s)>1 else '-',f1(s.median()),
         f'{f1(s.quantile(.25))}–{f1(s.quantile(.75))}', f'{f1(s.min())}–{f1(s.max())}']
    got=[re.sub(r'\s+',' ',str(x)).strip() for x in row]
    for k,(x,y) in enumerate(zip(got,exp)):
        ok+=1
        if x!=y: err+=1; print(f'T10 {a} {cur} col{k}: doc={x!r} sav={y!r}')

# ---- Table 60 against out/analysis.json mc_tests
mc={(t['var'],t['actor']):t for t in json.load(open('out/analysis.json'))['mc_tests']}
vm=json.load(open('v6/varmap.json'))
byl={}
for (v,a),t in mc.items(): byl[(t['label'],a)]=t
for row in T[49]['rows']:
    if len(row)<8 or str(row[0]).startswith('__BLOCK__'): continue
    if not str(row[0]).startswith('Objective'): continue
    a, lab = str(row[1]).strip(), str(row[2]).strip()
    t=byl.get((lab,a))
    ok+=1
    if t is None:
        err+=1; print(f'T49 {a}/{lab}: no matching Monte Carlo test'); continue
    p = '< .001' if t['p']<.001 else f'{t["p"]:.3f}'.lstrip('0')
    exp=[f'{t["chi2"]:.2f}',str(t['df']),str(t['N']),p]
    got=[re.sub(r'\s+',' ',str(x)).strip() for x in row[3:7]]
    for k,(x,y) in enumerate(zip(got,exp)):
        if x!=y: err+=1; print(f'T49 {a}/{lab} col{k}: doc={x!r} src={y!r}')
    if not t['sig']: err+=1; print(f'T49 {a}/{lab}: listed as significant but sig=False')
# are any significant tests missing from Table 60?
listed={(str(r[1]).strip(),str(r[2]).strip()) for r in T[49]['rows'] if len(r)>=8 and str(r[0]).startswith('Objective')}
for (lab,a),t in byl.items():
    if t['sig'] and (a,lab) not in listed:
        err+=1; print(f'T49 MISSING significant result: {a} / {lab} p={t["p"]}')
print(f'\nsample, income/age and association figures re-derived: {ok}   mismatches: {err}')
