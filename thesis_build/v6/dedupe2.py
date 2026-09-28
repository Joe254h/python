# -*- coding: utf-8 -*-
"""Second pass: the composite figures.

Six figures are drawn from several variables at once, so the first pass could
not match them to a table. Five of them show the same numbers as a table that
carries strictly more: exact counts, standard deviations, medians, quartiles or
the margins in shillings. Those figures go and the tables stay, by the same
rule as the first pass. The sixth, the institutional summary, has no single
table equivalent and stays.
"""
import json, re

ch4 = json.load(open('v6/ch4.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}

# figure file -> the table that carries strictly more of the same numbers
SUPERSEDED = {
    'f01_sample_by_site':   'Distribution of Respondents',
    'f16_price_actor_grade': 'Reported Mud Crab Prices by Actor Category and Size Grade',
    'f17_chain_share':      'Marketing Margins and the Distribution',
    'f18_price_site_actor': 'Mean Reported Mud Crab Price by Actor Category, BMU',
    'f19_fisher_share_site': 'First-Sale Price Spread Between Fishers and Middlemen',
}
title2num = {t['title']: n for n, t in T.items()}
def find(frag):
    for ttl, n in title2num.items():
        if ttl.startswith(frag):
            return n
    raise KeyError(frag)

drop = {}
for f, frag in SUPERSEDED.items():
    drop[f] = find(frag)

gone = [b['n'] for b in ch4 if b['k'] == 'fig' and b['f'] in drop]
print('figures superseded by a richer table:')
for b in ch4:
    if b['k'] == 'fig' and b['f'] in drop:
        print(f'   F{b["n"]:<3} {b["t"][:52]:54s} -> Table {drop[b["f"]]}')

out = [b for b in ch4 if not (b['k'] == 'fig' and b['f'] in drop)]

# renumber the figures, remapping every prose reference in one pass
old_f = [b['n'] for b in out if b['k'] == 'fig']
fmap = {o: i + 5 for i, o in enumerate(old_f)}
for b in out:
    if b['k'] == 'fig':
        b['n'] = fmap[b['n']]

FREF = re.compile(r'\bFigures\s+(\d+)\s*(?:to|and|–|-)\s*(\d+)|\bFigure\s+(\d+)\b')

def fix(text):
    def sub(m):
        if m.group(3):
            o = int(m.group(3))
            return f'Figure {fmap[o]}' if o in fmap else m.group(0)
        a, z = int(m.group(1)), int(m.group(2))
        keep = [fmap[o] for o in range(a, z + 1) if o in fmap]
        if not keep:
            return m.group(0)
        if len(keep) == 1:
            return f'Figure {keep[0]}'
        if keep == list(range(keep[0], keep[-1] + 1)) and len(keep) > 2:
            return f'Figures {keep[0]} to {keep[-1]}'
        return 'Figures ' + ', '.join(map(str, keep[:-1])) + f' and {keep[-1]}'
    return FREF.sub(sub, text)

for b in out:
    if b['k'] in ('p', 'bul', 'num', 'h1', 'h2', 'h3', 'h4'):
        b['t'] = fix(b['t'])

json.dump(out, open('v6/ch4.json', 'w'), ensure_ascii=False, indent=1)
print(f'\nfigures {len(old_f) + len(gone)} -> {len(old_f)}   tables unchanged at {len(T)}')
