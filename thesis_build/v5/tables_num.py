# -*- coding: utf-8 -*-
"""Sample distribution, price, margin and test tables. All carry the four actor
categories."""
import sys, json, numpy as np
sys.path.insert(0, 'v5')
from engine import DF, VL, ACT, BMU, ACTORS, SITES, NA, _MC, fmt_p
from scipy import stats

D = '—'
G = [('Large (Grade A)', 'price_large_0_2'), ('Medium (Grade B)', 'price_medium_0_2'),
     ('Small (Grade C)', 'price_small_0_2')]
OUT = []

def ser(var, mask):
    s = DF.loc[mask, var].dropna(); return s[s > 0]

# ---- Table 1: distribution of respondents -------------------------------
rows = []
for a in ACTORS:
    n_a = int((ACT == a).sum())
    rows.append([a] + [f'{int(((ACT==a)&(BMU==s)).sum())} '
                       f'({100*int(((ACT==a)&(BMU==s)).sum())/n_a:.1f}%)' for s in SITES]
                + [f'{n_a} (100.0%)'])
rows.append(['Total'] + [f'{int((BMU==s).sum())} ({100*int((BMU==s).sum())/96:.1f}%)'
                         for s in SITES] + ['96 (100.0%)'])
OUT.append(dict(num=1, title='Distribution of Respondents by Actor Category and BMU',
                headers=['Actor category'] + SITES + ['Total'],
                widths=[1700, 1250, 1250, 1150, 1400, 1300, 976], rows=rows, note=None))

# ---- income and age descriptives ----------------------------------------
def desc(s, money=True):
    if len(s) == 0: return [D] * 6
    f = (lambda x: f'{x:,.1f}') if money else (lambda x: f'{x:,.0f}')
    q1, q3 = np.percentile(s, [25, 75])
    return [str(len(s)), f(s.mean()), f(s.std(ddof=1)) if len(s) > 1 else '0.0',
            f(np.median(s)), f'{f(q1)}–{f(q3)}', f'{f(s.min())}–{f(s.max())}']
rows = []
for lab, var, money in [('Reported monthly mud crab income (KSh)', 'income_ksh_0_1', True),
                        ('Age in completed years', 'age_0_1', False)]:
    rows.append(['__BLOCK__' + lab] + [''] * 6)
    for a in ACTORS:
        rows.append([a] + desc(ser(var, ACT == a), money))
    rows.append(['All actors'] + desc(ser(var, ACT.notna()), money))
OUT.append(dict(num=900, title='Reported Monthly Income and Age of Respondents by Actor Category',
                headers=['Actor category', 'Valid n', 'M', 'SD', 'Mdn', 'IQR (Q1–Q3)', 'Range'],
                widths=[2100, 1000, 1250, 1150, 1150, 1500, 876], rows=rows, note=None))

# ---- prices by actor and grade ------------------------------------------
rows = []
for gl, var in G:
    rows.append(['__BLOCK__' + gl] + [''] * 6)
    for a in ACTORS:
        rows.append([a] + desc(ser(var, ACT == a)))
OUT.append(dict(num=901, title='Reported Mud Crab Prices by Actor Category and Size Grade',
                headers=['Actor category', 'Valid n', 'M', 'SD', 'Mdn', 'IQR (Q1–Q3)', 'Range'],
                widths=[1900, 950, 1200, 1100, 1100, 1550, 1226], rows=rows, note=None))

# ---- prices by actor, BMU and grade -------------------------------------
rows = []
for gl, var in G[:2]:
    rows.append(['__BLOCK__' + gl] + [''] * 5)
    for s_ in SITES:
        cells = []
        for a in ACTORS:
            v = ser(var, (ACT == a) & (BMU == s_))
            cells.append(f'{v.mean():,.1f} ({len(v)})' if len(v) else NA)
        rows.append([s_] + cells)
    rows.append(['All sites'] + [f'{ser(var, ACT==a).mean():,.1f} ({len(ser(var, ACT==a))})'
                                 if len(ser(var, ACT == a)) else NA for a in ACTORS])
OUT.append(dict(num=902, title='Mean Reported Mud Crab Price by Actor Category, BMU and Size Grade',
                headers=['BMU'] + [f'{a}\nM KSh/kg (n)' for a in ACTORS],
                widths=[1900, 1800, 1850, 1750, 1726], rows=rows, note=None))

# ---- Kruskal-Wallis ------------------------------------------------------
def kw(var, group, mask, levels):
    gs = [ser(var, mask & (group == lv)) for lv in levels]
    gs = [g for g in gs if len(g)]
    if len(gs) < 2: return None
    H, p = stats.kruskal(*gs)
    return H, len(gs) - 1, sum(len(g) for g in gs), p
rows = []
for lab, group, mask, levels in [
        ('Price compared across the four actor categories', ACT, ACT.notna(), ACTORS),
        ('Fisher price compared across the four BMUs', BMU, (ACT == 'Fisher') & BMU.isin(SITES[:4]), SITES[:4]),
        ('Middleman price compared across the three BMUs with traders', BMU,
         (ACT == 'Middleman') & BMU.isin(SITES[:3]), SITES[:3])]:
    rows.append(['__BLOCK__' + lab] + [''] * 4)
    for gl, var in G:
        r = kw(var, group, mask, levels)
        rows.append([gl] + ([f'{r[0]:.2f}', str(r[1]), str(r[2]), fmt_p(r[3])] if r else [D]*4))
rows.append(['__BLOCK__Hoteliers and exporters were not compared across BMUs because four of the '
             'five hoteliers and all four exporters operated outside the four BMU frames'] + [''] * 4)
OUT.append(dict(num=903, title='Kruskal–Wallis Comparisons of Reported Mud Crab Prices',
                headers=['Comparison', 'H', 'df', 'N', 'p'],
                widths=[3900, 1300, 900, 1000, 1926], rows=rows, note=None))

# ---- marketing margins ---------------------------------------------------
def m(var, a):
    s = ser(var, ACT == a); return float(s.mean()) if len(s) else None
rows = []; margins = {}
CHAINS = [('Large (Grade A) sold on to exporters', 'price_large_0_2', 'Exporter'),
          ('Large (Grade A) sold on to hoteliers', 'price_large_0_2', 'Hotelier'),
          ('Medium (Grade B) sold on to exporters', 'price_medium_0_2', 'Exporter')]
for lab, var, term in CHAINS:
    f, mid, end = m(var, 'Fisher'), m(var, 'Middleman'), m(var, term)
    rows.append(['__BLOCK__' + lab] + [''] * 4)
    for name, price, added, pctf in [
            ('Fisher (first sale)', f, f, None),
            ('Middleman', mid, mid - f, 100 * (mid - f) / f),
            (f'{term} (end of chain)', end, end - mid, 100 * (end - mid) / f)]:
        rows.append([name, f'{price:,.1f}', f'{added:,.1f}',
                     (f'{pctf:,.1f}' if pctf is not None else D), f'{100*added/end:.1f}'])
    other = 'Hotelier' if term == 'Exporter' else 'Exporter'
    rows.append([f'{other} (not in this chain)', D, D, D, D])
    margins[lab] = dict(fisher=round(f,1), middleman=round(mid,1), terminal=round(end,1),
                        f_share=round(100*f/end,1), m_share=round(100*(mid-f)/end,1),
                        t_share=round(100*(end-mid)/end,1))
OUT.append(dict(num=904,
                title='Marketing Margins and the Distribution of the Final Chain Price Across Actor Nodes',
                headers=['Market node', 'Mean price\n(KSh/kg)', 'Value retained or\nmargin added (KSh/kg)',
                         'Margin as % of the\nfisher price', '% of the final\nchain price'],
                widths=[2400, 1450, 1900, 1750, 1526], rows=rows, note=None))

# ---- first-sale spread ---------------------------------------------------
rows = []; site_sp = {}
for gl, var in G[:2]:
    rows.append(['__BLOCK__' + gl] + [''] * 5)
    for s_ in SITES:
        sf = ser(var, (ACT == 'Fisher') & (BMU == s_))
        sm = ser(var, (ACT == 'Middleman') & (BMU == s_))
        if len(sf) and len(sm):
            f, m2 = float(sf.mean()), float(sm.mean())
            rows.append([s_, f'{f:,.1f}', f'{m2:,.1f}', f'{m2-f:,.1f}',
                         f'{100*(m2-f)/f:.1f}', f'{100*f/m2:.1f}'])
            site_sp[f'{gl}|{s_}'] = dict(f=round(f,1), m=round(m2,1), spread=round(m2-f,1),
                                         share=round(100*f/m2,1), nf=len(sf), nm=len(sm))
        else:
            rows.append([s_, f'{sf.mean():,.1f}' if len(sf) else NA,
                         f'{sm.mean():,.1f}' if len(sm) else NA, NA, NA, NA])
OUT.append(dict(num=905, title='First-Sale Price Spread Between Fishers and Middlemen Within Each BMU',
                headers=['BMU', 'Fisher M\n(KSh/kg)', 'Middleman M\n(KSh/kg)', 'Spread\n(KSh/kg)',
                         'Spread as % of\nthe fisher price', 'Fisher price as % of\nthe middleman price'],
                widths=[1500, 1300, 1450, 1200, 1700, 1876], rows=rows, note=None))

# ---- significant associations -------------------------------------------
sig = sorted([r for r in _MC.values() if r.get('sig')],
             key=lambda r: (r['objective'], r['actor'], r['p']))
rows = [[f"Objective {r['objective']}", r['actor'], r['label'], f"{r['chi2']:.2f}",
         str(r['df']), str(r['N']), fmt_p(r['p']),
         f"[{r['ci'][0]:.3f}, {r['ci'][1]:.3f}]".replace('0.', '.')] for r in sig]
rows.append(['__BLOCK__No association with BMU reached the .05 level for hoteliers or exporters; '
             'neither group was sampled across enough BMUs for the test to be run'] + [''] * 7)
OUT.append(dict(num=906, title='Statistically Significant Actor-Specific Associations With BMU',
                headers=['Objective', 'Actor', 'Variable', 'χ²', 'df', 'N', 'p', '99% CI'],
                widths=[1100, 1150, 2350, 850, 600, 600, 800, 1576], rows=rows, note=None))

json.dump(OUT, open('v5/tables_num.json', 'w'), indent=1)
json.dump(dict(chain=margins, site=site_sp), open('v5/margins.json', 'w'), indent=1)
for t in OUT:
    print(f"T{t['num']:>4} | {len(t['rows']):>2} rows | {t['title'][:70]}")
