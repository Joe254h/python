# -*- coding: utf-8 -*-
"""Tighten Chapter Four's interpretive paragraphs.

These are the paragraphs that read the tables rather than report them, so
nothing here carries a cell value. Each is matched on its opening words and
replaced. No figure, p-value, table reference or claim changes.
"""
import json

P = 'v6/ch4_dedup.json'
ch4 = json.load(open(P))

REPL = {
 'Four conventions govern how the tables should be read.':
  'Four conventions govern how the tables should be read. Percentages are valid percentages '
  'within the actor category at that site, so the denominator is the number of respondents '
  'of that category who answered that item there, never the full 96. A hyphen means the '
  'category had no respondents at that site; a zero means it had respondents but none gave '
  'that response. The BMU p-value appears on the first row of each actor block, for fishers '
  'and middlemen only, because four of the five hoteliers and all four exporters operated '
  'outside the four BMU frames.',

 'This distribution sets the limits of the site comparisons.':
  'This distribution sets the limits of the site comparisons. No middleman was sampled at '
  'Msambweni, so middleman tests use the three sites where traders were interviewed. '
  'Msambweni is left out of those tables rather than shown as a column of zeros: that is a '
  'gap in the realised sample, not evidence that no middlemen work there.',

 'Considered together, Tables 8 to 12 and Figure 6':
  'Considered together, Tables 8 to 12 and Figure 6 describe a business structure that '
  'scales and formalises down the chain. Scale rose from fishers, almost uniformly '
  'small-scale, through middlemen, whose scale varied by site, to hoteliers at medium scale '
  'and exporters at large. Income followed the same gradient and licensing was rare '
  'upstream but universal downstream. Credit traced the line in reverse: fishers borrowed '
  'from middlemen, middlemen from exporters, exporters from banks, a single chain of '
  'dependency from the landing beach to the export market.',

 'Tables 13 and 14 together point to a fishery':
  'Tables 13 and 14 point to a fishery with very little institutional support. Most fishers '
  'learned the trade at home rather than through instruction, and fewer than one in twelve '
  'had received any training. Not one respondent at any node belonged to a cooperative, an '
  'association or a self-help group. The only formal structure in the chain was the market '
  'channel itself, which divided the domestic and international segments categorically. For '
  'Objective One the absence of any collective body is the most consequential finding: '
  'every actor here negotiates alone.',

 'That result needs reading with care.':
  'That result needs care. A near-perfect association between where a fisher lands and where '
  'his buyer sits is close to a tautology, and is reported for completeness rather than as a '
  'finding about market structure. What it establishes is that first sale is local: the '
  'buyer sits beside the landing site, not in a distant market the fisher could reach '
  'instead.',

 'Table 22 and Figures 12 to 14 show that protection':
  'Table 22 and Figures 12 to 14 show that protection of the product rises with distance '
  'from the water, and that its cost falls on whoever holds the crab at the time. A sack '
  'carried on foot and a Styrofoam box flown out are two ends of one handling problem, and '
  'the actor least able to absorb a loss uses the least protective method.',

 'Tables 23 to 27 and Figure 15 identify the mechanism':
  'Tables 23 to 27 and Figure 15 identify the mechanism by which value is captured '
  'downstream. A fisher can weigh a crab as accurately as anyone; what he cannot do is '
  'price the shell condition and claw size his buyer is paying for, or verify that the grade '
  'offered is the grade the animal deserves. The site variation in labelling compounds it. '
  'The survey recorded the word used, not a measured carapace width, so this is vocabulary '
  'rather than biology, and a Shimoni fisher and his buyer may not mean the same thing by '
  'large. That is the condition under which a grading dispute resolves in favour of the '
  'better-informed party.',

 'Tables 29 and 30 and Figure 17 describe the moment':
  'Tables 29 and 30 and Figure 17 describe the moment the terms of exchange are settled. The '
  'fisher sells at the beach, on the day, at a price the buyer sets, and is often paid at '
  'least partly in credit by that same buyer. Fixed at the fisher node and competitive at '
  'the middleman node are one transaction described from either end.',

 'Objective Two asks how the market is organised':
  'Objective Two asks how the market is organised, and concentration is the standard way of '
  'answering that. A textbook concentration ratio needs a census of the buyers at each '
  'landing site and the volume each handles; this survey recorded neither. What it did '
  'record is where each fisher took his catch for first sale, which supports a measure of a '
  'different kind: how far the harvesters at a site are spread across buying points, or '
  'gathered at one. The shares below are shares of harvesters, not of volume.',

 'Two cautions belong with these numbers.':
  'Two cautions belong with these numbers. They measure where harvesters take their catch, '
  'not how much crab each buying point handles, so a point many fishers name but that buys '
  'little from each would be overweighted; and they rest on the fishers sampled at a site '
  'rather than every fisher working there. Neither changes the direction: at three of the '
  'four BMUs more than two thirds of the harvesters interviewed carried their catch to one '
  'place, and more than three quarters dealt with one buyer when they got there.',

 'Set beside the concentration results, one finding needs care.':
  'Set beside the concentration results, one finding needs care. Majoreni was the most '
  'concentrated site on every measure in Table 40, yet it transmitted the largest share of '
  'the downstream price to its harvesters, while Vanga carried the most harvesters per '
  'trader (5.25 to one) and transmitted the least. Concentration of outlets and the price a '
  'harvester receives did not move together here. Nothing causal follows from three sites '
  'and a cross-sectional design, but it suggests that how many buying points exist matters '
  'less than how many sellers compete for each buyer, and it marks a question worth '
  'designing a study around.',

 'Table 45, Table 46 and Figure 19 show that each constraint':
  'Table 45, Table 46 and Figure 19 show each constraint following from the work the actor '
  'does. The fisher sells the same day at a price he does not set, so volatility reaches him '
  'first and the road stands between him and a buyer. The middleman holds stock, so he '
  'loses crabs and needs somewhere to hold them. The hotelier lives on tourist arrivals and '
  'the exporter on cargo space. For Objective Three the consequence is that no single '
  'chain-wide measure would reach all four, which is why the recommendations in Chapter Six '
  'are written by actor category.',

 'That contrast is the substantive finding of this subsection.':
  'That contrast is the substantive finding here. Information about how the fishery is '
  'managed reaches the commercially connected nodes and misses the harvesting node, even '
  'though the co-management structures built to carry it are anchored at the landing site. '
  'Since every actor relied on networking, information travels by the same relationship '
  'that sets the price.',

 'The large neutral response among fishers is not approval.':
  'The large neutral response among fishers is not approval. Set beside the 15.4% '
  'management-plan awareness in Table 50, it more plausibly reflects unfamiliarity with the '
  'policy environment than a settled judgement. The middlemen, aware of the management plan '
  'almost to a person, were also the group most willing to say the framework does not work, '
  'so the negative judgements here come from knowledge rather than ignorance.',

 'These are two views of one transaction.':
  'These are two views of one transaction. The fisher wants an alternative to the buyer in '
  'front of him; the middleman wants the price he pays and receives to hold still while he '
  'carries stock and credit risk. Splitting the difference will not reconcile them, because '
  'better market access for fishers means more competition for middlemen. Better price '
  'information and clearer grades reduce uncertainty for both without fixing a price.',

 'Three points belong with Table 53.':
  'Three points belong with Table 53. The tests carry no correction for multiple '
  'comparisons, so associations close to .05 are exploratory rather than established, and '
  'the Monte Carlo confidence interval is given alongside each p-value. The nine '
  'significant results cluster in three areas: who fishes where (age, marital status, '
  'training), how far and how they describe their catch (travel time, large- and small-crab '
  'size labels, first buyer location), and what middlemen worry about (main constraint). The '
  'absence of hoteliers and exporters is a limit of the frame, not a finding.',

 'Across the three objectives the same pattern recurs.':
  'Across the three objectives the same pattern recurs. Differences between actor categories '
  'were large and present on nearly every measure, from education and licensing through '
  'grading and quality control to price and the constraint each group names. Differences '
  'between Beach Management Units were far fewer: nine significant associations from '
  'sixty-eight tests, confined to age, marital status, training, travel time, size '
  'labelling, first buyer location and the middleman constraint.',
}

before = sum(len(b['t'].split()) for b in ch4 if b.get('k') in ('p', 'bul', 'num'))
hit = set()
for b in ch4:
    if b.get('k') != 'p':
        continue
    for opener, new in REPL.items():
        if b['t'].startswith(opener):
            b['t'] = new; hit.add(opener); break
missing = [o[:50] for o in REPL if o not in hit]
after = sum(len(b['t'].split()) for b in ch4 if b.get('k') in ('p', 'bul', 'num'))
if missing:
    print('NOT FOUND:')
    for m in missing: print('   ', m)
    raise SystemExit('some paragraphs did not match; nothing written')
json.dump(ch4, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'paragraphs rewritten: {len(hit)}')
print(f'Chapter Four prose: {before:,} -> {after:,} (saved {before - after:,})')
