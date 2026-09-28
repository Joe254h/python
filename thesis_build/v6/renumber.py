# -*- coding: utf-8 -*-
"""Number the tables in the order they appear in the chapter.

The market-structure tables were appended to the table set but inserted in the
middle of Objective Two, so the captions ran out of order. This renumbers every
Chapter Four table by its position, remaps the prose in Chapters Four to Six in
a single pass, and rewrites the table set to match. Figures are already in
order and are left alone.
"""
import json, re

ch4 = json.load(open('v6/ch4_dedup.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final_dedup.json'))}

order = [b['n'] for b in ch4 if b['k'] == 'table']
# Table 1 is the methods table in section 3.9, so Chapter Four starts at 2
tmap = {old: i + 2 for i, old in enumerate(order)}
if all(tmap[o] == o for o in order):
    print('already in order, nothing to do')
    raise SystemExit

for b in ch4:
    if b['k'] == 'table':
        b['n'] = tmap[b['n']]

REF = re.compile(r'\bTables\s+(\d+)\s*(?:to|and|–|-)\s*(\d+)|\bTable\s+(\d+)\b')

def fix(text):
    def sub(m):
        if m.group(3):
            o = int(m.group(3))
            return f'Table {tmap[o]}' if o in tmap else m.group(0)
        a, z = int(m.group(1)), int(m.group(2))
        new = [tmap[o] for o in range(a, z + 1) if o in tmap]
        if not new:
            return m.group(0)
        new.sort()
        if len(new) == 1:
            return f'Table {new[0]}'
        if new == list(range(new[0], new[-1] + 1)) and len(new) > 2:
            return f'Tables {new[0]} to {new[-1]}'
        if len(new) == 2:
            return f'Tables {new[0]} and {new[1]}'
        return 'Tables ' + ', '.join(map(str, new[:-1])) + f' and {new[-1]}'
    return REF.sub(sub, text)

n = 0
for b in ch4:
    if b['k'] in ('p', 'bul', 'num', 'h1', 'h2', 'h3', 'h4'):
        new = fix(b['t'])
        if new != b['t']:
            b['t'] = new; n += 1

ch56 = json.load(open('v5/ch56.json'))
m = 0
for b in ch56:
    if b['k'] in ('p', 'bul', 'num'):
        new = fix(b['t'])
        if new != b['t']:
            b['t'] = new; m += 1

newT = []
for old, new in sorted(tmap.items(), key=lambda kv: kv[1]):
    t = dict(T[old]); t['num'] = new
    newT.append(t)

json.dump(ch4, open('v6/ch4_dedup.json', 'w'), ensure_ascii=False, indent=1)
json.dump(newT, open('v6/tables_final_dedup.json', 'w'), ensure_ascii=False, indent=1)
json.dump(ch56, open('v5/ch56.json', 'w'), ensure_ascii=False, indent=1)

moved = {o: v for o, v in tmap.items() if o != v}
print(f'tables renumbered into document order: {len(moved)} moved')
for o, v in sorted(moved.items())[:12]:
    print(f'   T{o} -> T{v}')
print(f'prose blocks updated: Chapter Four {n}, Chapters Five and Six {m}')
nums = [b['n'] for b in ch4 if b['k'] == 'table']
print('now sequential 2..%d: %s' % (nums[-1], nums == list(range(2, 2 + len(nums)))))
