# -*- coding: utf-8 -*-
"""Name every exhibit in the prose, and correct two references.

After the de-duplication each variable appears once, so every table and figure
has to be pointed at by a sentence. Ten were left unnamed: a table whose
paragraph described it without naming it, and figures whose paragraph named the
table beside them. Two references were also wrong, because their table held two
variables that both became figures and the automatic mapping kept only one.
"""
import json, re

P = 'v6/ch4.json'
ch4 = json.load(open(P))

EDITS = [
    # ---- two references pointing at the wrong figure of a pair
    ('Nothing in this chapter expresses the structure of the chain more clearly than Figure 23.',
     'Nothing in this chapter expresses the structure of the chain more clearly than Figure 22.'),
    ('Figure 25 shows that youth involvement was rated low or very low',
     'Figure 24 shows that youth involvement was rated low or very low'),

    # ---- Table 1: the paragraph describes it without naming it
    ('Fishers accounted for 65 of the 96 respondents, middlemen for 22',
     'Table 1 shows that fishers accounted for 65 of the 96 respondents, middlemen for 22'),

    # ---- figures that stand beside a table covering other items
    ('Table 10 covers three indicators of business formality.',
     'Table 10 covers three indicators of business formality, and Figure 7 sets licensing, '
     'credit, training and collective membership side by side across the four actor categories.'),
    ('Source of crabs followed the same division',
     'Figure 8 shows that the source of crabs followed the same division'),
    ('As shown in Table 21, preparation became more elaborate at each step.',
     'Figure 12 shows that preparation became more elaborate at each step.'),
    ('They did not grade by the same rule.',
     'They did not grade by the same rule, and Figure 15 shows how far apart the criteria were.'),
    ('Table 28 divides the chain in two.',
     'Table 28 and Figure 18 divide the chain in two.'),
    ('Table 41 shows the same divergence in infrastructure.',
     'Table 41 and Figure 19 show the same divergence in infrastructure.'),
    ('Awareness of the instrument governing the fishery was far less evenly spread.',
     'Awareness of the instrument governing the fishery, shown in Figure 20, was far less '
     'evenly spread.'),

    # ---- exhibits covering the second half of a paragraph
    ('Preservation was reported only by the hoteliers',
     'Table 21 records preservation, which was reported only by the hoteliers'),
    ('On what would improve the system, every fisher named government support alone',
     'On what would improve the system, shown in Figure 23, every fisher named government '
     'support alone'),
    ('Diversification potential divided the chain:',
     'Diversification potential, in Figure 25, divided the chain:'),
]

n = 0
for old, new in EDITS:
    for b in ch4:
        if b['k'] in ('p', 'bul', 'num') and old in b['t']:
            b['t'] = b['t'].replace(old, new, 1)
            n += 1
            break
    else:
        print('  NOT FOUND:', old[:70])

json.dump(ch4, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'prose edits applied: {n} of {len(EDITS)}')

# ---- report anything still unnamed
miss = []
for i, b in enumerate(ch4):
    if b['k'] not in ('fig', 'table'):
        continue
    lab = 'Figure' if b['k'] == 'fig' else 'Table'
    win = [x for x in ch4[max(0, i - 3):i + 4] if x['k'] == 'p']
    if not any(re.search(rf'\b{lab} {b["n"]}\b', x['t']) for x in win):
        miss.append(f'{lab} {b["n"]}')
print('exhibits still not named by nearby prose:', len(miss), miss)
