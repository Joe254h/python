# -*- coding: utf-8 -*-
"""Cost of the de-duplication, before doing it.

Rule: one presentation per variable.
  - BMU association significant -> keep the TABLE (it carries all four actors,
    the site pattern, chi-square, df, p and the 99% CI) and drop the figure.
  - otherwise                   -> keep the FIGURE and drop that variable's
    block from the table; the non-significant p-value stays in the prose.
"""
import json, collections
ch4 = json.load(open('v6/ch4.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}
varmap = json.load(open('v6/varmap.json'))
dup = json.load(open('v6/dupes.json'))

drop_fig = sorted({d['fig'] for d in dup if d['sig']})
keep_fig_vars = {d['var'] for d in dup if not d['sig']}
sig_vars = {d['var'] for d in dup if d['sig']}
keep_fig_vars -= sig_vars                      # a variable is decided once

# which table blocks go
blocks = collections.defaultdict(list)
for n, t in T.items():
    for r in t['rows']:
        s = str(r[0])
        if s.startswith('__BLOCK__'):
            v = varmap.get(s[9:])
            blocks[n].append((s[9:], v))

emptied, thinned = [], []
for n, bl in blocks.items():
    if not bl:
        continue
    gone = [b for b in bl if b[1] in keep_fig_vars]
    if not gone:
        continue
    if len(gone) == len(bl):
        emptied.append((n, T[n]['title'][:56]))
    else:
        thinned.append((n, T[n]['title'][:46], len(gone), len(bl)))

print(f'figures dropped (their variable is significant, so the table stays): {len(drop_fig)}')
print('  ', drop_fig)
print()
print(f'tables removed entirely (every block in them is now shown as a figure): {len(emptied)}')
for n, t in sorted(emptied):
    print(f'   T{n:<3} {t}')
print()
print(f'tables that lose a block but survive: {len(thinned)}')
for n, t, g, tot in sorted(thinned):
    print(f'   T{n:<3} {t}   ({g} of {tot} blocks go)')
print()
figs = [b['n'] for b in ch4 if b['k'] == 'fig']
print(f'RESULT   figures {len(figs)} -> {len(figs) - len(drop_fig)}   '
      f'(plus 4 in Chapters One to Three)')
print(f'         tables  {len(T)} -> {len(T) - len(emptied)}')
