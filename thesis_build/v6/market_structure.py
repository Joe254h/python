# -*- coding: utf-8 -*-
"""Market structure measures the survey CAN support.

The review asked for concentration, margins and efficiency. None of the three
can be computed the textbook way here, because the survey interviewed actors
rather than censusing buyers and recorded no costs or transaction volumes. Each
one does, however, have a defensible counterpart in the data, and this works
out exactly what those are so the thesis reports them rather than only naming
what is missing.

  concentration : the buying points named at first sale, weighted by the share
                  of harvesters attached to each, plus the number of harvesters
                  per trader at each landing site
  margins       : the gross marketing margin and producer's share, then the
                  same figures net of the one cost the survey did measure,
                  which is physical mortality
  efficiency    : price dispersion within actor and grade, and the share of the
                  downstream price transmitted to the harvester
"""
import pyreadstat, pandas as pd, numpy as np, json

df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
VL = meta.variable_value_labels
ACT = {1.0: 'Fisher', 2.0: 'Middleman', 3.0: 'Hotelier', 4.0: 'Exporter'}
SITE = {1.0: 'Shimoni', 2.0: 'Majoreni', 3.0: 'Vanga', 4.0: 'Msambweni', 5.0: 'Other sites'}
SITES4 = ['Shimoni', 'Majoreni', 'Vanga', 'Msambweni']
df['_a'] = df['actor'].map(ACT)
df['_s'] = df['bmu'].map(SITE)
lab = lambda v: df[v].map(VL[v])

out = {}

# ===================================================== 1. CONCENTRATION
print('=' * 78)
print('1. CONCENTRATION AT FIRST SALE')
print('=' * 78)

f = df[df._a == 'Fisher'].copy()
f['_b1'] = f['buyer1_location_0_2'].map(VL['buyer1_location_0_2'])

def hhi(counts):
    """Herfindahl-Hirschman Index over shares, expressed 0-10,000."""
    tot = counts.sum()
    if tot == 0:
        return np.nan
    sh = counts / tot
    return float((sh ** 2).sum() * 10000)

overall = f['_b1'].value_counts()
n_overall = int(overall.sum())
sh = (overall / n_overall * 100).round(1)
print(f'\nFirst-buyer location, all fishers (n = {n_overall})')
for k, v in overall.items():
    print(f'   {k:20s} {v:3d}  {sh[k]:5.1f}%')
H = hhi(overall)
cr1 = sh.iloc[0]
cr2 = sh.iloc[:2].sum()
cr4 = sh.iloc[:4].sum()
print(f'   outlets named          : {len(overall)}')
print(f'   HHI                    : {H:,.0f}')
print(f'   CR1 / CR2 / CR4        : {cr1:.1f}% / {cr2:.1f}% / {cr4:.1f}%')
print(f'   numbers equivalent     : {10000 / H:.2f} outlets')
out['overall'] = dict(n=n_overall, outlets=int(len(overall)), hhi=round(H),
                      cr1=float(cr1), cr2=float(cr2), cr4=float(cr4),
                      neq=round(10000 / H, 2))

print('\nWithin each BMU')
rows = []
for s in SITES4:
    sub = f[f._s == s]
    c = sub['_b1'].value_counts()
    c = c[c > 0]
    if c.sum() == 0:
        continue
    H = hhi(c)
    top = c.index[0]
    rows.append(dict(site=s, n=int(c.sum()), outlets=int(len(c)), hhi=round(H),
                     cr1=round(c.iloc[0] / c.sum() * 100, 1), top=top,
                     neq=round(10000 / H, 2)))
    print(f'   {s:11s} n={int(c.sum()):3d}  outlets={len(c)}  HHI={H:6,.0f}  '
          f'CR1={c.iloc[0] / c.sum() * 100:5.1f}% ({top})  N_eq={10000 / H:.2f}')
out['by_site'] = rows

print('\nBuyers per seller')
bc = f['buyer_count_0_2'].dropna()
one = int((bc == 1).sum()); two = int((bc == 2).sum())
print(f'   one buyer  : {one:3d}  ({one / len(bc) * 100:.1f}%)')
print(f'   two buyers : {two:3d}  ({two / len(bc) * 100:.1f}%)')
print(f'   mean buyers per fisher : {bc.mean():.2f}')
out['buyers_per_seller'] = dict(n=int(len(bc)), one=one, two=two,
                                mean=round(float(bc.mean()), 2),
                                one_pct=round(one / len(bc) * 100, 1))

print('\nHarvesters per trader, by BMU')
rows = []
for s in SITES4:
    nf = int(((df._a == 'Fisher') & (df._s == s)).sum())
    nm = int(((df._a == 'Middleman') & (df._s == s)).sum())
    r = round(nf / nm, 2) if nm else None
    rows.append(dict(site=s, fishers=nf, middlemen=nm, ratio=r))
    print(f'   {s:11s} fishers={nf:3d}  middlemen={nm:3d}  '
          f'ratio={"no trader sampled" if not nm else f"{r:.2f} : 1"}')
nf = int((df._a == 'Fisher').sum()); nm = int((df._a == 'Middleman').sum())
print(f'   {"All BMUs":11s} fishers={nf:3d}  middlemen={nm:3d}  ratio={nf / nm:.2f} : 1')
out['ratio'] = rows
out['ratio_all'] = dict(fishers=nf, middlemen=nm, ratio=round(nf / nm, 2))

# ===================================================== 2. MARGINS
print()
print('=' * 78)
print('2. MARGINS')
print('=' * 78)

G = {'Large (Grade A)': 'price_large_0_2', 'Medium (Grade B)': 'price_medium_0_2'}
mean = {g: {a: df.loc[df._a == a, c].dropna().mean() for a in ACT.values()}
        for g, c in G.items()}

# physical loss: mortality band midpoints, in kg per day
MORT_MID = {'Frozen / no mortality': 0.0, '0.5-1 kg': 0.75, '4-5 kg': 4.5, 'Above 10 kg': 10.0}
CATCH_MID = {'2-3 kg': 2.5, '4-5 kg': 4.5, '5-10 kg': 7.5, 'Above 10 kg': 10.0}
f['_mort'] = f['mortality_0_2'].map(VL['mortality_0_2']).map(MORT_MID)
f['_catch'] = f['catch_daily_0_2'].map(VL['catch_daily_0_2']).map(CATCH_MID)
m = df[df._a == 'Middleman'].copy()
m['_mort'] = m['mortality_0_2'].map(VL['mortality_0_2']).map(MORT_MID)

loss_f = float((f['_mort'] / f['_catch']).dropna().mean() * 100)
print(f'\nFisher physical loss  : mean mortality {f["_mort"].mean():.2f} kg/day against '
      f'mean catch {f["_catch"].mean():.2f} kg/day  =  {loss_f:.1f}% of volume')
print(f'Middleman mortality   : mean {m["_mort"].mean():.2f} kg/day '
      f'(no volume handled was recorded, so no rate can be formed)')
out['loss'] = dict(fisher_mort=round(float(f['_mort'].mean()), 2),
                   fisher_catch=round(float(f['_catch'].mean()), 2),
                   fisher_loss_pct=round(loss_f, 1),
                   middleman_mort=round(float(m['_mort'].mean()), 2))

CHAINS = [('Large (Grade A)', 'Exporter'), ('Large (Grade A)', 'Hotelier'),
          ('Medium (Grade B)', 'Exporter')]
print('\nGross marketing margin and producer share, then net of measured physical loss')
rows = []
for g, end in CHAINS:
    pf, pm, pe = mean[g]['Fisher'], mean[g]['Middleman'], mean[g][end]
    gmm_m = (pm - pf) / pm * 100          # middleman margin as % of his selling price
    gmm_e = (pe - pm) / pe * 100          # end-node margin as % of his selling price
    ps = pf / pe * 100                    # producer's share of the end price
    ps_net = (pf * (1 - loss_f / 100)) / pe * 100
    tgm = (pe - pf) / pe * 100            # total gross marketing margin
    rows.append(dict(grade=g, end=end, pf=round(pf, 1), pm=round(pm, 1), pe=round(pe, 1),
                     gmm_middleman=round(gmm_m, 1), gmm_end=round(gmm_e, 1),
                     total_gmm=round(tgm, 1), producer_share=round(ps, 1),
                     producer_share_net=round(ps_net, 1)))
    print(f'\n   {g}, chain ending at the {end.lower()}')
    print(f'      fisher {pf:,.1f}  middleman {pm:,.1f}  {end.lower()} {pe:,.1f} KSh/kg')
    print(f'      middleman GMM {gmm_m:5.1f}%   {end.lower()} GMM {gmm_e:5.1f}%   '
          f'total GMM {tgm:5.1f}%')
    print(f'      producer share {ps:5.1f}%  ->  {ps_net:5.1f}% after the '
          f'{loss_f:.1f}% loss the fisher carries')
out['margins'] = rows

# ===================================================== 3. EFFICIENCY
print()
print('=' * 78)
print('3. PRICE DISPERSION AND TRANSMISSION')
print('=' * 78)
rows = []
print('\nCoefficient of variation of reported price')
for g, c in G.items():
    print(f'   {g}')
    for a in ACT.values():
        s = df.loc[df._a == a, c].dropna()
        if len(s) < 2:
            continue
        cv = s.std(ddof=1) / s.mean() * 100
        rows.append(dict(grade=g, actor=a, n=int(len(s)), mean=round(float(s.mean()), 1),
                         cv=round(float(cv), 1)))
        print(f'      {a:11s} n={len(s):3d}  M={s.mean():8,.1f}  CV={cv:5.1f}%')
out['cv'] = rows

print('\nShare of the middleman price transmitted to the fisher, by BMU')
rows = []
for g, c in G.items():
    for s in SITES4:
        fs = df[(df._a == 'Fisher') & (df._s == s)][c].dropna()
        ms = df[(df._a == 'Middleman') & (df._s == s)][c].dropna()
        if len(fs) == 0 or len(ms) == 0:
            continue
        t = fs.mean() / ms.mean() * 100
        rows.append(dict(grade=g, site=s, transmission=round(float(t), 1)))
        print(f'   {g:18s} {s:11s} {t:5.1f}%')
out['transmission'] = rows

json.dump(out, open('v6/market_structure.json', 'w'), indent=1)
print('\nwritten v6/market_structure.json')
