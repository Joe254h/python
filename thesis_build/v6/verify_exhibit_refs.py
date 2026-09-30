# -*- coding: utf-8 -*-
"""Check that the tables and figures a paragraph names belong to its own section.

Renumbering kept the prose consistent with itself but not with the section: a
summary paragraph that once read "Tables 18 to 20" still read that way after the
tables in its own section had become Table 22 and Figures 12 to 14. A number
that exists somewhere in the thesis is not a number that belongs here.

Deliberate cross-references to an exhibit in another section are legitimate and
are listed in ALLOW by the sentence that makes them.
"""
import json, re

ALLOW = [
 'Returning to Table 37',
 'Read against Table 12',
 'recalling from Table 16',
 'Set beside the concentration results',
 'Table 50 shows',
 'reported later in Table 35',
 'the 15.4% management-plan awareness in Table 50',
 'which Table 33 shows',
 'and Table 33 shows',
 'in Table 11',
 'sits oddly against Table 3',
 'the single-buyer pattern in Table 18',
 'Majoreni was the most concentrated site on every measure in Table 40',
]

ch4 = json.load(open('v6/ch4.json'))
RANGE = re.compile(r'\b(Tables|Figures)\s+(\d+)(?:\s*,\s*(\d+))?\s*(?:to|and|–|-)\s*(\d+)')
SINGLE = re.compile(r'\b(Table|Figure)\s+(\d+)')

sections, cur = [], None
for b in ch4:
    if b.get('k') in ('h1', 'h2', 'h3', 'h4'):
        cur = {'title': b['t'], 'tables': set(), 'figs': set(), 'ps': []}
        sections.append(cur); continue
    if cur is None:
        continue
    if b.get('k') == 'table': cur['tables'].add(b['n'])
    elif b.get('k') == 'fig': cur['figs'].add(b['n'])
    elif b.get('k') in ('p', 'bul', 'num'): cur['ps'].append(b['t'])

bad = 0
for s in sections:
    for t in s['ps']:
        for sent in re.split(r'(?<=[.;])\s+', t):
            if any(a in sent for a in ALLOW):
                continue
            want = {'Table': set(), 'Figure': set()}
            for m in RANGE.finditer(sent):
                kind = m.group(1)[:-1]
                got = [int(g) for g in m.groups()[1:] if g]
                want[kind] |= set(range(min(got), max(got) + 1))
            for m in SINGLE.finditer(RANGE.sub(' ', sent)):
                want[m.group(1)].add(int(m.group(2)))
            stray = sorted(want['Table'] - s['tables']), sorted(want['Figure'] - s['figs'])
            if any(stray):
                bad += 1
                print(f'  {s["title"][:42]:44s} names T{stray[0]} F{stray[1]}; '
                      f'section holds T{sorted(s["tables"])} F{sorted(s["figs"])}')
                print(f'      "{sent[:100]}"')
print(f'\nexhibit references naming an exhibit outside their own section: {bad}')
