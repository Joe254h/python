# -*- coding: utf-8 -*-
"""Independent re-derivation of every categorical cell straight from the .sav
with plain pandas, compared against what the thesis actually prints."""
import pyreadstat, pandas as pd, json, re, docx
from docx.oxml.ns import qn

df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
VL = meta.variable_value_labels
ACT = {1.0: 'Fisher', 2.0: 'Middleman', 3.0: 'Hotelier', 4.0: 'Exporter'}
SITE = {1.0: 'Shimoni', 2.0: 'Majoreni', 3.0: 'Vanga', 4.0: 'Msambweni', 5.0: 'Other sites'}
SITES = ['Shimoni', 'Majoreni', 'Vanga', 'Msambweni', 'Other sites']
df['_a'] = df['actor'].map(ACT)
df['_s'] = df['bmu'].map(SITE)
varmap = json.load(open('v6/varmap.json'))

def cell(var, lab, actor, site=None):
    sub = df[df._a == actor]
    if site is not None: sub = sub[sub._s == site]
    if len(sub) == 0: return '-'
    col = sub[var]; n = int(col.notna().sum())
    if n == 0: return '-'
    inv = {v: k for k, v in VL.get(var, {}).items()}
    code = inv.get(lab)
    if code is None: return '??' + lab
    c = int((col == code).sum())
    return f'{c} ({round(100.0*c/n,1):.1f}%)'

# ---- read the tables straight out of the finished thesis
d = docx.Document('v6/thesis.docx'); kids = list(d.element.body)
def ptx(el): return ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip()
caps = {}
for i, e in enumerate(kids):
    if e.tag == qn('w:p'):
        m = re.fullmatch(r'Table (\d+)', ptx(e))
        if m: caps[int(m.group(1))] = i
checked = mism = unmapped = 0
details = []
for num in sorted(caps):
    i = caps[num]; j = i + 1
    while kids[j].tag != qn('w:tbl'): j += 1
    rows = [[ptx(c) for c in r.findall(qn('w:tc'))] for r in kids[j].findall(qn('w:tr'))]
    hdr = rows[0]
    if len(hdr) != 9 or hdr[1] != 'Actor': continue
    cur = None
    for row in rows[1:]:
        if len(row) == 1:                       # spanner: names the variable
            cur = varmap.get(row[0])
            if cur is None: unmapped += 1
            continue
        if cur is None: continue
        actor = re.sub(r'\s*N\s*=.*$', '', row[1]).strip()
        if actor not in ACT.values(): continue
        lab = row[0]
        for k, site in enumerate([None] + SITES):
            got = row[2 + k]
            exp = cell(cur, lab, actor, site)
            checked += 1
            if got != exp:
                mism += 1
                if len(details) < 15:
                    details.append((num, cur, lab, actor, site or 'Overall', got, exp))
print(f're-derived from the .sav: {checked} cells   mismatches: {mism}   unmapped blocks: {unmapped}')
for x in details: print('   T%-3s %-26s %-28s %-10s %-12s doc=%-12s sav=%s' % x)
