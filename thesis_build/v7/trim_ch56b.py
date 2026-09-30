# -*- coding: utf-8 -*-
"""Merge the two closing sections of Chapter Five and tighten the synthesis.

Section 5.6 explained what the concentration, margin and efficiency measures do
and do not capture; Section 5.7 listed the study limitations. The last
paragraph of each said the same thing about missing cost and volume data, so the
two are now one section and the repetition is gone. The synthesis in 5.5 and
the chapter introductions are tightened, and 6.1 no longer describes the
four-label recommendation format that the recommendations no longer use.

Every figure, citation and table reference is unchanged.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'This chapter interprets the findings of Chapter Four against the literature':
  'This chapter interprets the findings of Chapter Four against the literature reviewed in '
  'Chapter Two. It takes the three objectives in turn, setting out the key findings, '
  'comparing them with previous research and drawing out the theoretical and practical '
  'implications. Section 5.5 brings the three objectives together under the '
  'structure-conduct-performance framework, and Section 5.6 states what the measures do and '
  'do not capture, along with the limitations that bound every claim made here.',

 'This chapter draws conclusions from the three objectives':
  'This chapter draws conclusions from the three objectives and sets out recommendations. '
  'Each recommendation rests on evidence reported in Chapter Four and names the body best '
  'placed to act. Recommendations the data cannot support are not made.',

 'Set against the structure-conduct-performance framework':
  'Set against the structure-conduct-performance framework that guided this study, the three '
  'objectives describe a single system. The structure is concentrated at the point of first '
  'sale: Table 40 gives an HHI of 2,371 across the four BMUs and 8,580 at the tightest of '
  'them, with 76.9% of harvesters selling to a single buyer and 2.95 harvesters for every '
  'trader sampled. Many small, unorganised sellers face fewer and better-capitalised '
  'buyers, entry downstream needs licences, capital and buyer contacts that upstream actors '
  'lack, and no collective body exists at any node to pool bargaining power.',

 'Performance is what that structure and conduct would predict.':
  'Performance is what that structure and conduct would predict. Reported monthly income ran '
  'from KSh 8,969 among fishers to KSh 90,000 among exporters. The fisher’s share of the '
  'end-of-chain price ran between 27.5% and 39.6%, the largest single share in every chain '
  'accrued at the node furthest from the water, and the total marketing margin ran from '
  '60.4% to 72.5% of the final price. Price dispersion was wide at the harvesting node and '
  'narrow after aggregation, a coefficient of variation of 31.8% against 6.8% for the large '
  'grade, which Green and Clark (2021) treat as a signature of weak integration at first '
  'sale. Losses were reported everywhere and measured nowhere against a common standard.',
}

n = 0
for b in ch56:
    if b.get('k') not in ('p', 'bul', 'num'):
        continue
    for opener, new in REPL.items():
        if b['t'].startswith(opener):
            b['t'] = new; n += 1; break
print(f'paragraphs rewritten: {n} of {len(REPL)}')

# ---------------------------------------------- merge 5.6 and 5.7 into one section
MERGED_TITLE = '5.6 What the Measures Capture and the Limitations of the Study'
MERGED = [
 'Three dimensions of market structure that the literature treats as standard cannot be '
 'computed here as a transaction survey would compute them. Each has a counterpart these '
 'data do support, reported in Chapter Four, and what each one is and is not measuring '
 'matters more than either claiming the full measure or leaving the gap unexplained.',

 'Concentration is measured over harvesters rather than volume. A textbook concentration '
 'ratio needs a census of buyers and the quantity each handles, and the survey recorded '
 'neither; it did record where every fisher took his catch, so Table 40 reports '
 'concentration over buying points weighted by the share of harvesters attached to each. '
 'The result is unambiguous: an HHI of 2,371 across the four BMUs and 8,580 at Majoreni, '
 'where a numbers-equivalent of 1.17 outlets means the harvesters face what is in practice '
 'a single buying point, and every BMU exceeds the 2,500 mark conventionally treated as '
 'high concentration. What the figures cannot say is how much crab passes through each '
 'point, so a buyer many fishers name but who takes little from each is overweighted, and a '
 'volume-weighted index remains out of reach.',

 'Margins are measured gross, and net of one cost. Table 43 gives the gross marketing '
 'margin at each node, a total marketing margin of 60.4% to 72.5% of the final price '
 'depending on the chain, and a producer’s share of 27.5% to 39.6%. The survey priced no '
 'transport, holding, ice, packaging or cost of capital, so none of these is a profit. It '
 'did measure physical mortality, and carrying that through cuts the producer’s share by '
 'roughly a tenth, to between 24.6% and 35.5%. A net margin in the accounting sense would '
 'still need the cost side of every transaction.',

 'Efficiency is approached through dispersion rather than cost. A full efficiency measure '
 'weighs the value added at a node against the cost of the services performed there, and '
 'again the cost side is missing. Two indicators that do not need it appear in Table 44. '
 'Price dispersion falls steadily down the chain, from a coefficient of variation of 31.8% '
 'among fishers to 14.9% among middlemen and 6.8% among exporters for the large grade, '
 'which says price uncertainty is carried almost entirely at the harvesting node. Price '
 'transmission, the share of the local middleman price reaching the fisher, ran from 53.6% '
 'at Vanga to 91.7% at Majoreni. Neither pretends to be a cost-based efficiency ratio.',

 'The sample was not fully probabilistic. Reliable lists were unavailable for middlemen, '
 'hoteliers and exporters, so referral and convenience procedures were used downstream, and '
 'the findings describe the respondents reached rather than population estimates for all '
 'Kwale County mud crab actors. The achieved fisher sample of 65 fell short of the '
 'calculated target of 83, a coverage rate of 78.3%, and the 18 fishers not reached may '
 'differ from those interviewed. Snowball sampling may over-represent actors with stronger '
 'trading connections, so the middleman and exporter findings in particular should be read '
 'with that in mind. Only five hoteliers and four exporters were sampled, no middleman was '
 'sampled at Msambweni, and only three fishers were interviewed there, which limits '
 'site-level precision.',

 'The design was cross-sectional and covered a single survey period, so seasonal variation '
 'in price, catch and mortality is not captured and no causal direction can be established. '
 'Prices, income and losses were self-reported and were not verified against transaction '
 'records. Sixty-eight categorical tests were run without a correction for multiple '
 'comparisons, so associations with probabilities close to .05 should be treated as '
 'exploratory. What remains genuinely unmeasured is narrower than it first appears: the '
 'volume behind each transaction, and the costs each actor carries. Both follow from an '
 'instrument designed as an actor inventory rather than a transaction survey, which is the '
 'right design for Objectives One and Three and a limiting one for the value-distribution '
 'part of Objective Two. Section 6.5 sets out the data collection that would close them.',
]

def span(title_start):
    i = next(k for k, b in enumerate(ch56)
             if b.get('k') in ('h2', 'h3') and b['t'].startswith(title_start))
    j = i + 1
    while j < len(ch56) and ch56[j].get('k') not in ('h1', 'h2', 'h3'):
        j += 1
    return i, j

i6, j6 = span('5.6 ')
i7, j7 = span('5.7 ')
assert j6 == i7, 'sections 5.6 and 5.7 are not adjacent'
head = dict(ch56[i6]); head['t'] = MERGED_TITLE
new = [head] + [{'k': 'p', 't': t} for t in MERGED]

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
ch56 = ch56[:i6] + new + ch56[j7:]
after = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
json.dump(ch56, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
