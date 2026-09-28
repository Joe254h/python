# -*- coding: utf-8 -*-
"""Every "<count> (<pct>%)" pair in a Chapter Four paragraph must appear as a
real cell in the table that paragraph is discussing."""
import json, re, collections
ch4 = json.load(open('v6/ch4.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}

cells = collections.defaultdict(set)      # table number -> {"n (p%)"}
for num, t in T.items():
    for row in t['rows']:
        for c in row:
            s = re.sub(r'\s+', ' ', str(c)).strip()
            m = re.fullmatch(r'(\d+) \(([\d.]+)%\)', s)
            if m: cells[num].add(s)
            m2 = re.fullmatch(r'([\d,.]+) \((\d+)\)', s)      # price tables: M (n)
            if m2: cells[num].add(s)

PAIR = re.compile(r'(\d+)\s*\(([\d.]+)%\)')
cur = None
checked = miss = 0
bad = []
for b in ch4:
    if b['k'] == 'table':
        cur = b['n']; continue
    if b['k'] != 'p' or cur is None: continue
    m = re.match(r'^Tables?\s+(\d+)', b['t'])
    ref = int(m.group(1)) if m else cur
    for mm in PAIR.finditer(b['t']):
        s = f'{mm.group(1)} ({mm.group(2)}%)'
        checked += 1
        # allow the paragraph's own table, the one it names, or its neighbours
        pool = set()
        for n in (ref, cur, ref - 1, ref + 1):
            pool |= cells.get(n, set())
        if s not in pool:
            miss += 1
            bad.append((ref, s, b['t'][max(0, mm.start()-70):mm.end()+20]))
print(f'prose "count (pct%)" pairs checked against real table cells: {checked}   not found: {miss}')
for r, s, ctx in bad: print(f'\n  [near Table {r}] {s}\n      …{ctx}…')
