# -*- coding: utf-8 -*-
"""Remove the remaining AI writing tells from the chapter prose.

Twelve em dashes used as parenthetical breaks become commas or brackets, and a
handful of stock constructions are rewritten: "worth stating plainly", "should
not be read as", "not merely X but Y". Numeric en dashes and Kruskal-Wallis
keep theirs, because those are ranges and a compound name.

No figure, citation or claim changes.
"""
import json, re

EDITS = [
 # ---- parenthetical em dashes
 ('Every table carries all four actor categories — fisher, middleman, hotelier and '
  'exporter — so that',
  'Every table carries all four actor categories (fisher, middleman, hotelier and '
  'exporter) so that'),
 ('was largest at every site where traders were sampled — 6 (54.5%) at Shimoni, 3 '
  '(42.9%) at Majoreni and 2 (50.0%) at Vanga — and',
  'was largest at every site where traders were sampled, 6 (54.5%) at Shimoni, 3 (42.9%) '
  'at Majoreni and 2 (50.0%) at Vanga, and'),
 ('exporters relied on banks — a single chain of credit dependency running from the '
  'landing beach',
  'exporters relied on banks, a single chain of credit dependency running from the '
  'landing beach'),
 ('every respondent in all four actor categories — 96 of 96 — said',
  'every respondent in all four actor categories, 96 of 96, said'),
 ('a matter of vocabulary rather than biology — but a Shimoni fisher',
  'a matter of vocabulary rather than biology. A Shimoni fisher'),
 ('the arrangement was credit in every case — 21 middlemen and 5 hoteliers, 100.0% of '
  'each —',
  'the arrangement was credit in every case, 21 middlemen and 5 hoteliers, 100.0% of each,'),
 ('the group most willing to say the framework does not work — which suggests',
  'the group most willing to say the framework does not work, which suggests'),

 # ---- stock constructions
 ('Where that difference comes from is worth stating plainly, because the two nodes did '
  'not move together.',
  'The two nodes did not move together, and that is where the difference comes from.'),
 ('Set beside the concentration results this produces a finding worth stating carefully.',
  'Set beside the concentration results, one finding needs care.'),
 ('the actor categories are not merely different occupations but successive positions of '
  'unequal formality and unequal access to finance.',
  'the actor categories are successive positions of unequal formality and unequal access '
  'to finance, not simply different occupations.'),
 ('The large neutral response among fishers should not be read as approval.',
  'The large neutral response among fishers is not approval.'),
 ('The large neutral response among fishers on the existence of a policy framework should '
  'not be read as approval;',
  'The large neutral response among fishers on the existence of a policy framework is not '
  'approval;'),
 ('and should not be treated as established.',
  'and is treated here as provisional.'),
]

total = 0
for path in ('v6/ch4_dedup.json', 'v5/ch56.json'):
    blocks = json.load(open(path))
    n = 0
    for b in blocks:
        if b['k'] not in ('p', 'bul', 'num'):
            continue
        for old, new in EDITS:
            if old in b['t']:
                b['t'] = b['t'].replace(old, new)
                n += 1
    json.dump(blocks, open(path, 'w'), ensure_ascii=False, indent=1)
    print(f'  {path}: {n} edits')
    total += n
print(f'total: {total} of {len(EDITS)} patterns applied')

# ---- report what is left
left = []
for path in ('v6/ch4_dedup.json', 'v5/ch56.json'):
    for b in json.load(open(path)):
        if b['k'] in ('p', 'bul', 'num') and '—' in b['t']:
            for m in re.finditer(r'[^.]*—[^.]*', b['t']):
                left.append(re.sub(r'\s+', ' ', m.group(0)).strip()[:110])
print(f'em dashes remaining: {len(left)}')
for x in left:
    print('   ', x)
