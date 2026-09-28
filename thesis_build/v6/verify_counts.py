# -*- coding: utf-8 -*-
"""Check the "<k> of <n> <actors>" and "all <n> <actors>" claims in the prose:
<n> must be a valid n that actually appears in the table being discussed."""
import json, re, collections
ch4 = json.load(open('v6/ch4.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}

# valid n per (table, actor) as printed in the Actor column, plus every count
# that appears in any cell of that table
ns = collections.defaultdict(set)
counts = collections.defaultdict(set)
for num, t in T.items():
    for row in t['rows']:
        for c in row:
            s = str(c)
            m = re.fullmatch(r'(\w+) N = (\d+)', s.strip())
            if m: ns[(num, m.group(1).lower())].add(int(m.group(2)))
            m2 = re.fullmatch(r'\s*(\d+) \([\d.]+%\)\s*', s)
            if m2: counts[num].add(int(m2.group(1)))
            m3 = re.fullmatch(r'\s*[\d,.]+ \((\d+)\)\s*', s)
            if m3: ns[(num, 'any')].add(int(m3.group(1)))

ACTW = {'fisher': 'fisher', 'fishers': 'fisher', 'middleman': 'middleman',
        'middlemen': 'middleman', 'hotelier': 'hotelier', 'hoteliers': 'hotelier',
        'exporter': 'exporter', 'exporters': 'exporter', 'respondent': None,
        'respondents': None}
OF = re.compile(r'\b(\d+)\s+of\s+(?:the\s+)?(\d+)\s+([a-z]+)')
ALL = re.compile(r'\ball\s+(\d+)\s+([a-z]+)')
cur = None; checked = 0; bad = []
for b in ch4:
    if b['k'] == 'table': cur = b['n']; continue
    if b['k'] != 'p' or cur is None: continue
    m = re.match(r'^Tables?\s+(\d+)', b['t'])
    ref = int(m.group(1)) if m else cur
    pool = set()
    for n in (ref, cur, ref - 1, ref + 1, ref + 2):
        for a in ('fisher', 'middleman', 'hotelier', 'exporter', 'any'):
            pool |= ns.get((n, a), set())
    for mm in list(OF.finditer(b['t'])) + list(ALL.finditer(b['t'])):
        g = mm.groups()
        tot, word = (int(g[1]), g[2]) if len(g) == 3 else (int(g[0]), g[1])
        if word not in ACTW: continue
        checked += 1
        if tot in pool or tot in (96, 65, 63, 22, 5, 4): continue
        bad.append((ref, mm.group(0), b['t'][max(0, mm.start()-60):mm.end()+25]))
print(f'"k of n <actor>" / "all n <actor>" claims checked: {checked}   bases not found in the table: {len(bad)}')
for r, s, ctx in bad: print(f'\n  [near Table {r}] {s!r}\n      …{ctx}…')
