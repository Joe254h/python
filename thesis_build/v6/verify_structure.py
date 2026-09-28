# -*- coding: utf-8 -*-
"""Re-derive every figure in the market-structure tables from the .sav and
compare it against what the thesis prints."""
import pyreadstat, pandas as pd, numpy as np, json, re, docx
import sys
sys.path.insert(0, 'v6')
import tablenum as TN

from docx.oxml.ns import qn

df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
VL = meta.variable_value_labels
df['_a'] = df['actor'].map({1.: 'Fisher', 2.: 'Middleman', 3.: 'Hotelier', 4.: 'Exporter'})
df['_s'] = df['bmu'].map({1.: 'Shimoni', 2.: 'Majoreni', 3.: 'Vanga',
                          4.: 'Msambweni', 5.: 'Other sites'})
SITES = ['Shimoni', 'Majoreni', 'Vanga', 'Msambweni']
f = df[df._a == 'Fisher'].copy()
f['_b1'] = f['buyer1_location_0_2'].map(VL['buyer1_location_0_2'])

d = docx.Document('v6/thesis.docx')
kids = list(d.element.body)
def ptx(e): return ''.join(t.text or '' for t in e.iter(qn('w:t'))).strip()
caps = {}
for i, e in enumerate(kids):
    if e.tag == qn('w:p'):
        m = re.fullmatch(r'Table (\d+)', ptx(e))
        if m:
            j = i + 1
            while kids[j].tag != qn('w:tbl'):
                j += 1
            caps[int(m.group(1))] = [[ptx(c) for c in r.findall(qn('w:tc'))]
                                     for r in kids[j].findall(qn('w:tr'))]

ok = bad = 0
def chk(label, got, exp):
    global ok, bad
    ok += 1
    if str(got).strip() != str(exp).strip():
        bad += 1
        print(f'   {label}: doc={got!r}  sav={exp!r}')

def hhi(c):
    s = c / c.sum()
    return (s ** 2).sum() * 10000

# ---- Table 50: concentration
for row in caps[TN.CONCENTRATION][1:]:
    s = row[0]
    if s == 'All four BMUs':
        c = f['_b1'].value_counts()
    elif s in SITES:
        c = f[f._s == s]['_b1'].value_counts()
        c = c[c > 0]
    else:
        continue
    H = hhi(c)
    chk(f'T{TN.CONCENTRATION} {s} n', row[1], str(int(c.sum())))
    chk(f'T{TN.CONCENTRATION} {s} outlets', row[2], str(len(c)))
    chk(f'T{TN.CONCENTRATION} {s} CR1', row[4], f'{c.iloc[0] / c.sum() * 100:.1f}%')
    chk(f'T{TN.CONCENTRATION} {s} HHI', row[5], f'{round(H):,}')
    chk(f'T{TN.CONCENTRATION} {s} Neq', row[6], f'{10000 / H:.2f}')

# ---- Table 51: buyer options and the ratio
for row in caps[TN.BUYERS][1:]:
    s = row[0]
    sub = f if s == 'All four BMUs' else f[f._s == s]
    b = sub['buyer_count_0_2'].dropna()
    one = int((b == 1).sum())
    chk(f'T{TN.BUYERS} {s} n', row[1], str(len(b)))
    chk(f'T{TN.BUYERS} {s} one buyer', row[2], f'{one} ({one / len(b) * 100:.1f}%)')
    chk(f'T{TN.BUYERS} {s} mean', row[3], f'{b.mean():.2f}')
    if s == 'All four BMUs':
        nf = int((df._a == 'Fisher').sum()); nm = int((df._a == 'Middleman').sum())
    else:
        nf = int(((df._a == 'Fisher') & (df._s == s)).sum())
        nm = int(((df._a == 'Middleman') & (df._s == s)).sum())
    chk(f'T{TN.BUYERS} {s} fishers', row[4], str(nf))
    chk(f'T{TN.BUYERS} {s} middlemen', row[5], str(nm))
    chk(f'T{TN.BUYERS} {s} ratio', row[6], f'{nf / nm:.2f} : 1' if nm else 'no trader sampled')

# ---- Table 52: margins
G = {'Large (Grade A)': 'price_large_0_2', 'Medium (Grade B)': 'price_medium_0_2'}
mean = {g: {a: df.loc[df._a == a, c].dropna().mean() for a in
            ['Fisher', 'Middleman', 'Hotelier', 'Exporter']} for g, c in G.items()}
MM = {'Frozen / no mortality': 0., '0.5-1 kg': .75, '4-5 kg': 4.5, 'Above 10 kg': 10.}
CM = {'2-3 kg': 2.5, '4-5 kg': 4.5, '5-10 kg': 7.5, 'Above 10 kg': 10.}
loss = float((f['mortality_0_2'].map(VL['mortality_0_2']).map(MM) /
              f['catch_daily_0_2'].map(VL['catch_daily_0_2']).map(CM)).dropna().mean() * 100)
for row in caps[TN.GMM][1:]:
    m = re.match(r'(.+?) sold on to (\w+)s$', row[0])
    if not m:
        continue
    g, end = m.group(1), m.group(2).capitalize()
    pf, pm, pe = mean[g]['Fisher'], mean[g]['Middleman'], mean[g][end]
    chk(f'T{TN.GMM} {g}/{end} fisher', row[1], f'{pf:,.1f}')
    chk(f'T{TN.GMM} {g}/{end} middleman', row[2], f'{pm:,.1f}')
    chk(f'T{TN.GMM} {g}/{end} final', row[3], f'{pe:,.1f}')
    chk(f'T{TN.GMM} {g}/{end} mid GMM', row[4], f'{(pm - pf) / pm * 100:.1f}%')
    chk(f'T{TN.GMM} {g}/{end} end GMM', row[5], f'{(pe - pm) / pe * 100:.1f}%')
    chk(f'T{TN.GMM} {g}/{end} total', row[6], f'{(pe - pf) / pe * 100:.1f}%')
    chk(f'T{TN.GMM} {g}/{end} share', row[7], f'{pf / pe * 100:.1f}%')
    chk(f'T{TN.GMM} {g}/{end} net', row[8], f'{pf * (1 - loss / 100) / pe * 100:.1f}%')

# ---- Table 53: dispersion and transmission
sect = None
for row in caps[TN.DISPERSION][1:]:
    if len(row) == 1:
        sect = 'cv' if 'Coefficient' in row[0] else 'tr'
        continue
    g = row[0]
    if g not in G:
        continue
    if sect == 'cv':
        for k, a in enumerate(['Fisher', 'Middleman', 'Hotelier', 'Exporter']):
            s = df.loc[df._a == a, G[g]].dropna()
            exp = f'{s.std(ddof=1) / s.mean() * 100:.1f}%' if len(s) > 1 else '-'
            chk(f'T{TN.DISPERSION} CV {g}/{a}', row[1 + k], exp)
    else:
        for k, st in enumerate(['Shimoni', 'Majoreni', 'Vanga']):
            fs = df[(df._a == 'Fisher') & (df._s == st)][G[g]].dropna()
            ms = df[(df._a == 'Middleman') & (df._s == st)][G[g]].dropna()
            exp = f'{fs.mean() / ms.mean() * 100:.1f}%' if len(fs) and len(ms) else '-'
            chk(f'T{TN.DISPERSION} transmission {g}/{st}', row[5 + k], exp)

print(f'market-structure figures re-derived: {ok}   mismatches: {bad}')
