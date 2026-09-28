# -*- coding: utf-8 -*-
"""Find every variable presented both as a table block and as a figure."""
import json, re, collections
ch4 = json.load(open('v6/ch4.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}
varmap = json.load(open('v6/varmap.json'))          # block label -> variable
mc = {(t['var'], t['actor']): t for t in json.load(open('out/analysis.json'))['mc_tests']}

# ---- figure -> variable, from the chart scripts
FIGVAR = {}
for path in ('v3/charts.py', 'v5/extra_charts.py'):
    src = open(path).read()
    for m in re.finditer(r"(?:clustered_actor|stacked_actor|hbar_actor)\(\s*'([\w.]+)'[^)]*?'(f\d+_\w+)'", src, re.S):
        FIGVAR[m.group(2)] = m.group(1)
    for m in re.finditer(r"by_site\(\s*'([\w.]+)'\s*,\s*'(\w+)'[^)]*?'(f\d+_\w+)'", src, re.S):
        FIGVAR[m.group(3)] = m.group(1)

figs = {b['n']: b for b in ch4 if b['k'] == 'fig'}

# ---- table -> variables
TVAR = {}
for n, t in T.items():
    vs = []
    for r in t['rows']:
        s = str(r[0])
        if s.startswith('__BLOCK__'):
            v = varmap.get(s[9:])
            if v:
                vs.append(v)
    TVAR[n] = vs

var2tab = collections.defaultdict(list)
for n, vs in TVAR.items():
    for v in vs:
        var2tab[v].append(n)


def sig(var):
    hits = [t for (vv, a), t in mc.items() if vv == var]
    best = [t for t in hits if t['sig']]
    return best[0] if best else None


print(f'{"FIG":>4} {"file":28s} {"variable":24s} {"in table(s)":12s} sig?')
print('-' * 86)
dup = []
for n, b in sorted(figs.items()):
    v = FIGVAR.get(b['f'])
    if not v:
        print(f'{n:>4} {b["f"]:28s} {"(composite / derived)":24s} {"-":12s} -')
        continue
    ts = var2tab.get(v, [])
    s = sig(v)
    tag = f"{s['actor']} p={s['p']:.3f}" if s else 'ns'
    print(f'{n:>4} {b["f"]:28s} {v:24s} {str(ts):12s} {tag}')
    if ts:
        dup.append((n, b['f'], v, ts, bool(s)))
print()
print(f'figures duplicating a table block: {len(dup)} of {len(figs)}')
print(f'  of those, the BMU association is significant for: {sum(1 for d in dup if d[4])}')
json.dump([{'fig': d[0], 'file': d[1], 'var': d[2], 'tables': d[3], 'sig': d[4]} for d in dup],
          open('v6/dupes.json', 'w'), indent=1)
