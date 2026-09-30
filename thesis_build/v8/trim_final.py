# -*- coding: utf-8 -*-
"""Last pass on Chapters Five and Six, and restore two citations.

ACDI/VOCA (2005) and Mahmud and Mamun (2013) were cited only in the Key
Findings subsection removed from Chapter Five, so both reference entries would
have gone with it. The multi-stage chain point they support belongs with the
grading discussion and is restored there.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'Every actor said they graded,':
  'Multi-stage chains of this kind, in which harvesters are separated from export buyers by '
  'one or more aggregation and trading nodes, have been described for Bangladesh, the '
  'Philippines and coastal Tanzania (ACDI/VOCA, 2005; Mahmud & Mamun, 2013; Sultana et al., '
  '2018). Every actor here said they graded, but not by the same rule: all 65 fishers used '
  'weight alone while 95.5% of middlemen and every hotelier and exporter combined size, '
  'weight, shell condition and claw size. Jacinto (2004) identifies this kind of '
  'informational asymmetry as a determinant of how value is distributed in small-scale '
  'fisheries.',

 'The four actor categories differ systematically and in the same direction':
  'The four actor categories differ systematically and in the same direction on almost every '
  'characteristic measured. Fishers are younger, schooled to primary level or below, '
  'small-scale, minimally licensed, untrained and un-diversified, and borrow from the '
  'middlemen who buy from them; middlemen are older, more experienced and better capitalised; '
  'hoteliers and exporters are formally qualified, fully licensed and operating at a scale '
  'upstream actors do not reach. None belonged to a cooperative or a self-help group.',

 'The chain runs as a functional sequence':
  'The chain runs as a functional sequence from harvesting through aggregation to processing '
  'and export, with the information used to assign value concentrated downstream: fishers '
  'graded on weight alone while every other category used four criteria, and formal quality '
  'control and contact with the final buyer sat entirely downstream. The fisher retained '
  '27.5% to 39.6% of the price the crab eventually fetched, the middleman added 15.5% to '
  '20.0%, and 44.4% to 57.0% was added at the final buyer. The first-sale gap was set '
  'locally: Majoreni fishers held 91.7% of the middleman price for large crabs where Shimoni '
  'and Vanga fishers held close to 54%. Price follows position in the chain, control of the '
  'grading rule and access to alternative buyers, not harvesting effort.',

 'Constraints arise at different points':
  'Constraints follow the work each actor does: unstable prices and poor roads for fishers, '
  'mortality and inadequate aggregation facilities for middlemen, seasonality for hoteliers, '
  'freight and flight risk for exporters. Barriers to market access were close to universal, '
  'no actor had adopted new equipment or conducted market research, and management-plan '
  'awareness reached traders and exporters while missing fishers and hoteliers, so '
  'improvement requires coordinated but actor-specific measures.',

 'The South Coast mud crab market is commercially active and institutionally uneven.':
  'The South Coast mud crab market is commercially active and institutionally uneven. Fishers '
  'supply the product with almost no institutional support, while middlemen and downstream '
  'actors hold the grading, the logistics and the connection to high-value buyers. Site '
  'matters for the age of the fishing population, the words used for grades, the price '
  'fishers receive and the constraint middlemen name, but the steadier divide runs between '
  'market nodes. Improvement should start where the terms of exchange are set: a shared '
  'grading standard, a reliable public price record, better live-crab handling, licensing '
  'people can obtain, and communication that reaches harvesters as dependably as traders.',

 'Packaging became more protective downstream':
  'Packaging became more protective downstream, from sacks to crates to Styrofoam, and '
  'reported mortality rose with the volume each actor held; survival and quality in the live '
  'trade turn on handling, containment and transport (FAO, 2025). The weakness is not that no '
  'care was taken, since fishers tied claws and middlemen cleaned and sorted, but that '
  'neither procedures nor losses were documented against a shared standard, so the cost of '
  'mortality cannot be priced into a grade.',

 'The hotelier medium-grade mean of KSh 380.0 per kilogram does not fit':
  'The hotelier medium-grade mean of KSh 380.0 per kilogram does not fit, sitting below the '
  'fisher price for the same grade and far below the same respondents’ large-crab mean of KSh '
  '2,200.0. The entries may refer to a different product form, unit or transaction, or may be '
  'a field-entry error. They were retained for fidelity and excluded from the chain '
  'calculation, but should be confirmed against the questionnaires first.',

 'Why men dominate harvesting here is not something these data can settle':
  'Why men dominate harvesting is not something these data can settle, but three mechanisms '
  'fit. Harvesting is done on foot in mangrove creeks at low spring tides, often at night and '
  'away from the village, carrying mobility and safety costs that fall unequally on women '
  '(Mirera et al., 2013; Moser et al., 2005); landing-site registers and BMU membership have '
  'historically enrolled men; and the credit relationship runs through established trading '
  'ties new entrants do not have.',

 'Each constraint follows from the work the actor does.':
  'Each constraint follows from the work the actor does. The fisher sells the same day at a '
  'price he does not set, so volatility reaches him first; the middleman holds stock, so he '
  'loses crabs, mortality being named by half of them and by all four Vanga middlemen; the '
  'hotelier feels the season and the exporter the freight. One chain-wide intervention will '
  'not reach all four.',

 'Fishers chose market-access improvement, 86.2% of them':
  'Fishers chose market-access improvement, 86.2% of them, while middlemen chose price '
  'stability, 95.5%: two views of one exchange. Better market access for fishers means more '
  'competition for middlemen, so splitting the difference will not reconcile them, whereas '
  'better price information and clearer grades reduce uncertainty for both.',
}

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
hit = set()
for b in ch56:
    if b.get('k') not in ('p', 'bul', 'num'):
        continue
    for opener, new in REPL.items():
        if opener in hit or not b['t'].startswith(opener):
            continue
        b['t'] = new; hit.add(opener); break
missing = [o[:58] for o in REPL if o not in hit]
if missing:
    print('NOT FOUND, nothing saved:')
    for m in missing: print('   ', m)
    raise SystemExit(1)
after = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
json.dump(ch56, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'paragraphs rewritten: {len(hit)}')
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
