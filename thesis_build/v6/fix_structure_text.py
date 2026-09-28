# -*- coding: utf-8 -*-
"""Bring the discussion into line with the market-structure measures now
reported in Chapter Four.

Section 5.6 had said concentration, margins and efficiency could not be
measured. Each now has a counterpart the data support and Chapter Four reports
it, so the section states what each measure does and does not capture, and what
remains genuinely out of reach. Chapters Five and Six live in ch56.json, so the
edits belong there and not in the assembled document.
"""
import json

MS = json.load(open('v6/market_structure.json'))
o = MS['overall']
site = {r['site']: r for r in MS['by_site']}
m0, m1, m2 = MS['margins']
lo = MS['loss']
bp = MS['buyers_per_seller']
ra = MS['ratio_all']

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REWRITE = [
 ('5.6 What This Study Could Not Measure',
  '5.6 What the Structure Measures Do and Do Not Capture'),

 ('Three dimensions of market structure that the literature treats as standard',
  'Three dimensions of market structure that the literature treats as standard '
  'cannot be computed here the way a transaction survey would compute them. Each '
  'has a counterpart these data do support, reported in Chapter Four, and setting '
  'out what each one is and is not measuring matters more than either claiming the '
  'full measure or leaving the gap unexplained.'),

 ('Market concentration could not be computed.',
  'Concentration is measured, but over harvesters rather than volume. A textbook '
  'concentration ratio needs a census of buyers and the quantity each handles, and '
  'the survey recorded neither. It did record where every fisher took his catch, '
  'so Table 50 reports concentration over buying points weighted by the share of '
  f'harvesters attached to each. The result is unambiguous: an HHI of {o["hhi"]:,} '
  f'across the four BMUs and {site["Majoreni"]["hhi"]:,} at Majoreni, where the '
  f'numbers-equivalent of {site["Majoreni"]["neq"]:.2f} outlets means the '
  'harvesters there face what is in practice a single buying point. Every BMU '
  'exceeds the 2,500 mark conventionally treated as high concentration. What these '
  'figures cannot say is how much crab passes through each point, so a buyer many '
  'fishers name but that takes little from each is overweighted. A volume-weighted '
  'index remains out of reach.'),

 ('Net marketing margins could not be estimated.',
  'Margins are measured gross, and net of one cost. Table 52 reports the gross '
  'marketing margin at each node, the total marketing margin, which ran from '
  f'{m2["total_gmm"]:.1f}% to {m1["total_gmm"]:.1f}% of the final price depending '
  f'on the chain, and the producer’s share, which ran from '
  f'{m1["producer_share"]:.1f}% to {m2["producer_share"]:.1f}%. The survey priced '
  'no transport, holding, ice, packaging or cost of capital, so none of these is a '
  'profit. It did measure physical mortality, and carrying that through cuts the '
  f'producer’s share by roughly a tenth, to between '
  f'{m1["producer_share_net"]:.1f}% and {m2["producer_share_net"]:.1f}%. A net '
  'margin in the accounting sense would still require the cost side of every '
  'transaction, which this instrument did not collect.'),

 ('Marketing efficiency could not be assessed.',
  'Efficiency is approached through dispersion rather than cost. A full efficiency '
  'measure weighs the value added at a node against the cost of the services '
  'performed there, and again the cost side is missing. Two indicators that do not '
  'need it are reported in Table 53. Price dispersion falls steadily down the '
  'chain, from a coefficient of variation of 31.8% among fishers to 14.9% among '
  'middlemen and 6.8% among exporters for the large grade, which says that price '
  'uncertainty is carried almost entirely at the harvesting node. Price '
  'transmission, the share of the local middleman price reaching the fisher, ran '
  'from 53.6% at Vanga to 91.7% at Majoreni. Both bear directly on how well the '
  'market moves information and value, without pretending to be a cost-based '
  'efficiency ratio.'),

 ('These three gaps share one cause.',
  'What remains genuinely unmeasured is narrower than it first appears: the volume '
  'behind each transaction, and the costs each actor carries. Both follow from an '
  'instrument designed as an actor inventory rather than a transaction survey, '
  'which is the right design for Objectives One and Three and a limiting one for '
  'the value-distribution part of Objective Two. Section 6.5 sets out the data '
  'collection that would close them.'),
]

n = 0
for opener, new in REWRITE:
    for b in ch56:
        if b['k'] in ('p', 'h2', 'h3') and b['t'].strip().startswith(opener):
            b['t'] = new
            n += 1
            break
    else:
        print('  NOT FOUND:', opener[:60])

# ------------------------------------------- the SCP synthesis gains numbers
for b in ch56:
    if b['k'] != 'p':
        continue
    t = b['t']
    if t.startswith('Set against the structure-conduct-performance framework'):
        b['t'] = t.replace(
            'The structure is concentrated at the point of first sale.',
            'The structure is concentrated at the point of first sale, and Table 50 '
            f'puts a number on it: an HHI of {o["hhi"]:,} across the four BMUs and '
            f'{site["Majoreni"]["hhi"]:,} at the tightest of them, with '
            f'{bp["one_pct"]:.1f}% of harvesters selling to a single buyer and '
            f'{ra["ratio"]:.2f} harvesters for every trader sampled.')
        n += 1
    elif t.startswith('Performance is what that structure and conduct would predict'):
        b['t'] = t.replace(
            'Price dispersion was wide at the harvesting node and narrow after aggregation,',
            'The total marketing margin ran from '
            f'{m2["total_gmm"]:.1f}% to {m1["total_gmm"]:.1f}% of the final price, and '
            'price dispersion was wide at the harvesting node and narrow after '
            'aggregation, a coefficient of variation of 31.8% against 6.8% for the '
            'large grade,')
        n += 1

# --------------------------------- the price-distribution discussion section
for b in ch56:
    if b['k'] == 'p' and b['t'].startswith('Reported prices rose at every node'):
        b['t'] = b['t'].rstrip() + (
            ' Expressed as marketing margins, the chain took between '
            f'{m2["total_gmm"]:.1f}% and {m1["total_gmm"]:.1f}% of the final price '
            'before it reached the harvester, and the concentration figures in '
            'Table 50 describe the structure within which that split is settled: '
            f'an HHI of {o["hhi"]:,} across the four BMUs, and {bp["one_pct"]:.1f}% '
            'of harvesters dealing with a single buyer.')
        n += 1
        break

json.dump(ch56, open(P, 'w'), ensure_ascii=False, indent=1)
print('Chapter Five edits applied:', n)
