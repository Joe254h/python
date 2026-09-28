# -*- coding: utf-8 -*-
"""The appendix must cover every variable the thesis reports and must agree
with Chapter Four wherever the two overlap."""
import json, re, docx, pyreadstat
from docx.oxml.ns import qn
A = json.load(open('v6/appendix.json'))
varmap = json.load(open('v6/varmap.json'))
df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
lbl2var = {v: k for k, v in varmap.items()}

need = set(varmap.values())
covered = set()
for b in A:
    if b['k'] != 'rawtable': continue
    m = re.match(r'^(.*?) \* actor Crosstabulation', b['title'])
    if not m: continue
    lab = m.group(1)
    v = varmap.get(lab)
    if v: covered.add(v)
print('variables the thesis reports:', len(need))
print('covered by Appendix A.1     :', len(covered))
gap = sorted(need - covered)
print('not covered                 :', len(gap), gap)

# ---- appendix overall column must equal the thesis Overall column
ACT = {1.0:'Fisher',2.0:'Middleman',3.0:'Hotelier',4.0:'Exporter'}
df['_a'] = df['actor'].map(ACT)
VL = meta.variable_value_labels
def cell(var, lab, actor):
    s = df.loc[df._a == actor, var]
    n = int(s.notna().sum())
    if n == 0: return '-'
    inv = {v: k for k, v in VL.get(var, {}).items()}
    code = inv.get(lab)
    if code is None: return '?'
    c = int((s == code).sum())
    return f'{c} ({100*c/n:.1f}%)'
ok = bad = 0
for b in A:
    if b['k'] != 'rawtable': continue
    m = re.match(r'^(.*?) \* actor Crosstabulation', b['title'])
    if not m: continue
    v = varmap.get(m.group(1))
    if not v: continue
    for row in b['rows']:
        if row[0] == 'Total': continue
        for k, a in enumerate(['Fisher','Middleman','Hotelier','Exporter']):
            got, exp = row[1+k], cell(v, row[0], a)
            ok += 1
            if got != exp:
                bad += 1
                if bad <= 10: print(f'   {v} / {row[0]} / {a}: appendix={got!r} sav={exp!r}')
print(f'appendix cells re-derived from the .sav: {ok}   mismatches: {bad}')
