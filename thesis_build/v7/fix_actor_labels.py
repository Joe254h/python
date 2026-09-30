# -*- coding: utf-8 -*-
"""Print the actor label once per block, not on every row.

The Actor column repeated "Fisher N = 65" against each response category, so a
five-category variable printed it five times before the middleman rows began.
It now appears on the first row of each actor's block and is blank underneath,
which is how a grouped column is normally set.
"""
import json

P = 'v6/tables_final_dedup.json'
T = json.load(open(P))

blanked = touched = 0
for t in T:
    h = t.get('headers') or []
    # only the nine-column actor-by-BMU tables, where the Actor column heads a
    # block. In the significant-associations table the Actor column is data,
    # one value per row, and blanking a repeat there loses information.
    if len(h) != 9 or h[1] != 'Actor' or h[2] != 'Overall':
        continue
    prev = None
    changed = False
    for r in t['rows']:
        if str(r[0]).startswith('__BLOCK__'):
            prev = None                      # a new variable restarts the grouping
            continue
        cur = str(r[1]).strip()
        if not cur:
            continue
        if cur == prev:
            r[1] = ''
            blanked += 1
            changed = True
        else:
            prev = cur
    touched += changed

json.dump(T, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'tables regrouped: {touched}   repeated actor labels blanked: {blanked}')

# the generator too, so a rebuild from the .sav does the same
p = 'v5/engine.py'
s = open(p).read()
old = """            rows.append([c, actor_lbl, cell(var, c, a)] +"""
new = """            # the actor label heads its block and is blank on the rows below
            rows.append([c, actor_lbl if k == 0 else '', cell(var, c, a)] +"""
if old in s:
    open(p, 'w').write(s.replace(old, new, 1))
    print('v5/engine.py updated for future rebuilds')
else:
    print('v5/engine.py already grouped, or its shape has changed')
