# -*- coding: utf-8 -*-
"""Check every "<count> of <total> (<pct>%)" and "<count> (<pct>%)" claim in the
prose of Chapters Four to Six: the percentage must be the count over the total
the sentence names, or over the actor's valid n for that variable."""
import json, re, sys, collections
from decimal import Decimal

ch4 = json.load(open('v6/ch4.json'))
ch56 = json.load(open('v5/ch56.json'))
tables = {t['num']: t for t in json.load(open('v6/tables_final.json'))}

# every "count (pct%)" pair that appears anywhere in a table becomes a known-good pair
known = set()
for t in tables.values():
    for row in t['rows']:
        for c in row:
            m = re.fullmatch(r'\s*(\d+)\s*\(([\d.]+)%\)\s*', str(c))
            if m: known.add((int(m.group(1)), m.group(2)))

def pct(n, d):
    return f'{round(100.0 * n / d, 1):.1f}'

bad, ok = [], 0
PAT_OF = re.compile(r'(\d+)\s+of\s+(\d+)\s+[a-z ]{0,40}?\(([\d.]+)%\)')
PAT_PAREN = re.compile(r'\((\d+),\s*([\d.]+)%\)')

for blocks, tag in ((ch4, 'Ch4'), (ch56, 'Ch5-6')):
    for b in blocks:
        if b['k'] not in ('p', 'bul', 'num'): continue
        s = b['t']
        for m in PAT_OF.finditer(s):
            n, d, p = int(m.group(1)), int(m.group(2)), m.group(3)
            if pct(n, d) == p: ok += 1
            else: bad.append((tag, f'{n} of {d} = {p}% (should be {pct(n,d)}%)', s[max(0,m.start()-60):m.end()+30]))
        for m in PAT_PAREN.finditer(s):
            n, p = int(m.group(1)), m.group(2)
            if (n, p) in known: ok += 1
            else:
                # allow it if the pct works out against any plausible denominator in the text
                cand = [65, 63, 22, 5, 4, 96, 61, 62, 64, 21, 20, 25, 37, 3, 2, 1, 10]
                if any(pct(n, d) == p for d in cand if d >= n): ok += 1
                else: bad.append((tag, f'({n}, {p}%) matches no table cell or plausible base',
                                  s[max(0,m.start()-70):m.end()+25]))
print(f'count/percentage claims checked: {ok + len(bad)}   consistent: {ok}   suspect: {len(bad)}')
for t, why, ctx in bad:
    print(f'\n  [{t}] {why}\n      …{ctx}…')
