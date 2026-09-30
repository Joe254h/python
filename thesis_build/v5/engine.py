# -*- coding: utf-8 -*-
"""Table engine in the candidate's own layout.

Columns: Characteristic / response | Actor (with N) | Overall | Shimoni |
Majoreni | Vanga | Msambweni | Other sites | BMU p-value.
Every table carries all four actor categories as row blocks, so fishers,
middlemen, hoteliers and exporters appear in each one.

A hyphen means the actor category had no respondents at that site. A zero
means they had respondents there but none gave that response. The BMU
p-value sits on the first row of each actor block and is shown only for
fishers and middlemen, the two groups with enough site coverage to test.
"""
import pyreadstat, json, numpy as np

DF, META = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
VL = META.variable_value_labels
LBL = META.column_names_to_labels
ACTORS = ['Fisher', 'Middleman', 'Hotelier', 'Exporter']
SITES = ['Shimoni', 'Majoreni', 'Vanga', 'Msambweni', 'Other sites']
ACT = DF['actor'].map(VL['actor'])
BMU = DF['bmu'].map(VL['bmu'])
NA = '-'

_MC = {}
for _r in json.load(open('out/analysis.json'))['mc_tests']:
    _MC[(_r['var'], _r['actor'])] = _r

def fmt_p(p):
    return '< .001' if p < .001 else f'{p:.3f}'.lstrip('0')

def vals(var, mask=None):
    s = DF[var]
    if var in VL:
        s = s.map(VL[var])
    if mask is not None:
        s = s[mask]
    return s.dropna()

def categories(var, order=None):
    cats = sorted({str(x) for x in vals(var)})
    if order:
        head = [c for c in order if c in cats]
        return head + [c for c in cats if c not in head]
    return cats

def valid_n(var, actor, site=None):
    m = (ACT == actor)
    if site is not None:
        m = m & (BMU == site)
    return int(len(vals(var, m)))

def sampled(actor, site):
    """Was this actor category sampled at this site at all?"""
    return int(((ACT == actor) & (BMU == site)).sum()) > 0

def cell(var, cat, actor, site=None):
    m = (ACT == actor)
    if site is not None:
        if not sampled(actor, site):
            return NA
        m = m & (BMU == site)
    s = vals(var, m)
    if len(s) == 0:
        return NA
    n = int((s.astype(str) == cat).sum())
    return f'{n} ({100*n/len(s):.1f}%)'

def pvalue(var, actor):
    r = _MC.get((var, actor))
    return fmt_p(r['p']) if r else ''

def var_block(var, order=None, label=None):
    """Rows for one variable: each response category repeated per actor."""
    rows = []
    cats = categories(var, order)
    for a in ACTORS:
        n_a = valid_n(var, a)
        actor_lbl = f'{a} N = {n_a}' if n_a else f'{a} N = 0'
        p = pvalue(var, a) if a in ('Fisher', 'Middleman') else ''
        for k, c in enumerate(cats):
            # the actor label heads its block and is blank on the rows below
            rows.append([c, actor_lbl if k == 0 else '', cell(var, c, a)] +
                        [cell(var, c, a, s) for s in SITES] +
                        [p if k == 0 else ''])
    return rows

HEADERS = ['Characteristic / response', 'Actor', 'Overall'] + SITES + ['BMU p-value']
WIDTHS = [1850, 1250, 900, 820, 820, 760, 900, 880, 846]

def table(num, title, specs):
    rows = []
    for spec in specs:
        var, order, label = (spec, None, None) if isinstance(spec, str) else \
                            (spec + (None,) * 3)[:3]
        rows.append(['__BLOCK__' + (label or LBL.get(var, var))] + [''] * 8)
        rows += var_block(var, order)
    return dict(num=num, title=title, headers=HEADERS, widths=WIDTHS, rows=rows, note=None)

if __name__ == '__main__':
    t = table(2, 'Age Group of Fishers, Middlemen, Hoteliers and Exporters by BMU',
              [('age_group_0_1', ['Under 18', '18-35', '36-49', '50-60', 'Over 60'])])
    print(' | '.join(t['headers']))
    for r in t['rows']:
        print(' | '.join(str(x) for x in r))
