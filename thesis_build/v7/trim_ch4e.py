# -*- coding: utf-8 -*-
"""Correct four wrong exhibit references and drop the last of the stale notes.

Four summary paragraphs still named the table numbers their sections carried
before the tables were renumbered, so they pointed at tables in other sections
altogether. Each now names the exhibits it is actually summarising.

Seven sentences left over from the notes that used to sit under the figures
repeat a claim made earlier in the same section. They add nothing and the last
of them turned a summary paragraph into a note about a blank column.
"""
import json

P = 'v6/ch4_dedup.json'
ch4 = json.load(open(P))

FIX = [
 # ---- wrong exhibit references
 ('Tables 18 to 20 show that protection of the product rises',
  'Table 22 and Figures 12 to 14 show that protection of the product rises'),
 ('Read together, Tables 24 and 25 show a chain',
  'Read together, Figure 16 and Table 28 show a chain'),
 ('Tables 35 and 36 show that each constraint follows',
  'Table 45, Table 46 and Figure 19 show that each constraint follows'),
 ('Read against Objective Three, Tables 37, 38 and 42 say',
  'Read against Objective Three, Tables 47 to 49 say'),

 # ---- sentences that repeat a claim already made in the same section
 (' Preparation moves from tying claws at the harvesting node to cleaning, sorting and '
  'grading downstream.', ''),
 (' Hoteliers did not complete this item.', ''),
 (' Hoteliers reported no mortality because crabs were frozen on arrival.', ''),
 (' The payment item was not completed by exporters.', ''),
 (' Fishers and hoteliers described the price as fixed by the buyer; middlemen and '
  'exporters described their own pricing as competitive.', ''),
 (' No fisher at Majoreni reported awareness of the plan.', ''),
 (' No hotelier or exporter agreed that the market is well structured.', ''),
 (' Fishers and middlemen named opposite priorities.', ''),
 (' No respondent in any category rated youth involvement as high.', ''),
]

before = sum(len(b['t'].split()) for b in ch4 if b.get('k') in ('p', 'bul', 'num'))
hits = {}
for b in ch4:
    if b.get('k') not in ('p', 'bul', 'num'):
        continue
    for old, new in FIX:
        if old in b['t']:
            b['t'] = b['t'].replace(old, new).strip()
            hits[old[:52]] = hits.get(old[:52], 0) + 1
after = sum(len(b['t'].split()) for b in ch4 if b.get('k') in ('p', 'bul', 'num'))
json.dump(ch4, open(P, 'w'), ensure_ascii=False, indent=1)

missed = [o[:52] for o, _ in FIX if o[:52] not in hits]
for k, v in hits.items():
    print(f'  {v}x  {k}')
if missed:
    print('NOT FOUND:')
    for m in missed: print('   ', m)
print(f'\nChapter Four prose: {before:,} -> {after:,} (saved {before - after:,})')
