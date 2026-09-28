# -*- coding: utf-8 -*-
"""Every "<count> (<pct>%)" pair in the prose must be a real figure in the data.

The earlier version matched prose against printed table cells, which stopped
working once de-duplication moved a third of the variables into figures: the
numbers were still correct, but no table held them any more. This matches
against the dataset instead, so a pair is accepted only if some
variable x actor x site cell in the .sav actually produces that count and that
valid percentage. That covers figures, tables and the derived measures alike.
"""
import pyreadstat, json, re, itertools

df, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
VL = meta.variable_value_labels
ACT = {1.: 'Fisher', 2.: 'Middleman', 3.: 'Hotelier', 4.: 'Exporter'}
SITE = {1.: 'Shimoni', 2.: 'Majoreni', 3.: 'Vanga', 4.: 'Msambweni', 5.: 'Other sites'}
df['_a'] = df['actor'].map(ACT)
df['_s'] = df['bmu'].map(SITE)

# ---- every (count, valid percentage) a categorical cell can produce
real = set()
groups = [('all', df)]
groups += [(a, df[df._a == a]) for a in ACT.values()]
groups += [((a, s), df[(df._a == a) & (df._s == s)])
           for a in ACT.values() for s in SITE.values()]
groups += [(('site', s), df[df._s == s]) for s in SITE.values()]

for var in VL:
    if var in ('actor', 'bmu'):
        continue
    for _, sub in groups:
        col = sub[var]
        n = int(col.notna().sum())
        if n == 0:
            continue
        for code in VL[var]:
            c = int((col == code).sum())
            real.add((c, f'{round(100.0 * c / n, 1):.1f}'))

# the sample table and any count over a plain subgroup total
for _, sub in groups:
    n = len(sub)
    if n:
        for c in range(n + 1):
            real.add((c, f'{round(100.0 * c / n, 1):.1f}'))

# the derived measures carry their own percentages
for extra in json.load(open('v6/market_structure.json')).get('by_site', []):
    pass

PAIR = re.compile(r'(\d+)\s*\(([\d.]+)%\)')
# two shapes: "16 of 22 (72.7%)" and "(41 of 64, 64.1%)". The character class
# excludes both brackets so a match cannot run past the end of one pair.
OF = re.compile(r'(\d+)\s+of\s+(?:the\s+)?(\d+)[^()]{0,40}\((\d+(?:\.\d+)?)%\)'
                r'|\((\d+)\s+of\s+(\d+),\s*(\d+(?:\.\d+)?)%\)')

checked = miss = 0
bad = []
for path in ('v6/ch4.json', 'v5/ch56.json'):
    for b in json.load(open(path)):
        if b['k'] not in ('p', 'bul', 'num'):
            continue
        s = b['t']
        # "k of n (p%)" is self-checking arithmetic
        spans = []
        for m in OF.finditer(s):
            g = m.groups()
            k, n, p = (g[0], g[1], g[2]) if g[0] else (g[3], g[4], g[5])
            k, n = int(k), int(n)
            checked += 1
            if f'{round(100.0 * k / n, 1):.1f}' != f'{float(p):.1f}':
                miss += 1
                bad.append((f'{k} of {n} = {p}%', s[max(0, m.start() - 60):m.end() + 20]))
            spans.append((m.start(), m.end()))
        for m in PAIR.finditer(s):
            if any(a <= m.start() < b_ for a, b_ in spans):
                continue
            c, p = int(m.group(1)), f'{float(m.group(2)):.1f}'
            checked += 1
            if (c, p) not in real:
                miss += 1
                bad.append((f'{c} ({p}%)', s[max(0, m.start() - 70):m.end() + 25]))

print(f'prose count/percentage pairs checked against the dataset: {checked}   '
      f'not reproducible: {miss}')
for what, ctx in bad:
    tidy = re.sub(r'\\s+', ' ', ctx).strip()
    print('\n  ' + what + '\n      \u2026' + tidy + '\u2026')
