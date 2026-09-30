# -*- coding: utf-8 -*-
"""Tighten the synthesis, the limitations and the conclusions.

The conclusions in 6.2 state for the third time what Chapter Four summarised
and Chapter Five discussed, so they carry the most repetition in the thesis and
take the deepest cut. Every figure and citation is kept.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'Set against the structure-conduct-performance framework':
  'Set against the structure-conduct-performance framework, the three objectives describe a '
  'single system. The structure is concentrated at first sale: Table 40 gives an HHI of '
  '2,371 across the four BMUs and 8,580 at the tightest, with 76.9% of harvesters selling to '
  'a single buyer and 2.95 harvesters for every trader sampled. Many small, unorganised '
  'sellers face fewer and better-capitalised buyers, entry downstream needs licences, '
  'capital and buyer contacts the upstream actors lack, and no collective body exists at any '
  'node.',

 'Performance is what that structure and conduct would predict.':
  'Performance is what that structure and conduct would predict. Reported monthly income ran '
  'from KSh 8,969 among fishers to KSh 90,000 among exporters. The fisher’s share of the '
  'end-of-chain price ran between 27.5% and 39.6%, the largest single share accrued furthest '
  'from the water, and the total marketing margin ran from 60.4% to 72.5%. Price dispersion '
  'was wide at the harvesting node and narrow after aggregation, a coefficient of variation '
  'of 31.8% against 6.8% for the large grade, which Green and Clark (2021) treat as a '
  'signature of weak integration at first sale.',

 'This has a practical edge.':
  'This has a practical edge. Measures aimed only at production, better gear or bigger '
  'catches, are unlikely to shift how value is distributed, because the binding constraint '
  'is not how many crabs come ashore but the terms on which they change hands. Three things '
  'decide those terms: the grading rule, whether a fisher has independent price information, '
  'and the credit relationship. All three operate in the moment the catch changes hands.',

 'Concentration is measured over harvesters rather than volume.':
  'Concentration is measured over harvesters rather than volume. A textbook ratio needs a '
  'census of buyers and the quantity each handles, and the survey recorded neither; it did '
  'record where every fisher took his catch, so Table 40 reports concentration over buying '
  'points weighted by the share of harvesters attached to each. An HHI of 2,371 across the '
  'four BMUs and 8,580 at Majoreni, where a numbers-equivalent of 1.17 outlets means the '
  'harvesters face what is in practice a single buying point, puts every BMU above the 2,500 '
  'mark conventionally treated as high concentration. What the figures cannot say is how '
  'much crab passes through each point, so a buyer many fishers name but who takes little '
  'from each is overweighted.',

 'Margins are measured gross, and net of one cost.':
  'Margins are measured gross, and net of one cost. Table 43 gives the gross marketing '
  'margin at each node, a total marketing margin of 60.4% to 72.5% of the final price '
  'depending on the chain, and a producer’s share of 27.5% to 39.6%. No transport, holding, '
  'ice, packaging or cost of capital was priced, so none of these is a profit. Physical '
  'mortality was measured, and carrying it through cuts the producer’s share by roughly a '
  'tenth, to between 24.6% and 35.5%.',

 'Efficiency is approached through dispersion rather than cost.':
  'Efficiency is approached through dispersion rather than cost, because a full efficiency '
  'measure weighs value added at a node against the cost of the services performed there and '
  'the cost side is missing. Two indicators that do not need it appear in Table 44. Price '
  'dispersion falls steadily down the chain, from a coefficient of variation of 31.8% among '
  'fishers to 14.9% among middlemen and 6.8% among exporters for the large grade, so price '
  'uncertainty is carried almost entirely at the harvesting node. Price transmission, the '
  'share of the local middleman price reaching the fisher, ran from 53.6% at Vanga to 91.7% '
  'at Majoreni.',

 'The sample was not fully probabilistic.':
  'The sample was not fully probabilistic. Reliable lists were unavailable for middlemen, '
  'hoteliers and exporters, so referral and convenience procedures were used downstream, and '
  'the findings describe the respondents reached rather than population estimates for all '
  'Kwale County mud crab actors. The achieved fisher sample of 65 fell short of the '
  'calculated target of 83, a coverage rate of 78.3%, and the 18 fishers not reached may '
  'differ from those interviewed. Snowball sampling may over-represent actors with stronger '
  'trading connections. Only five hoteliers and four exporters were sampled, no middleman '
  'was sampled at Msambweni, and only three fishers were interviewed there, which limits '
  'site-level precision.',

 'The design was cross-sectional and covered a single survey period,':
  'The design was cross-sectional and covered a single survey period, so seasonal variation '
  'in price, catch and mortality is not captured and no causal direction can be established. '
  'Prices, income and losses were self-reported and not verified against transaction '
  'records. Sixty-eight categorical tests were run without a correction for multiple '
  'comparisons, so associations close to .05 are exploratory. What remains genuinely '
  'unmeasured is narrower than it first appears: the volume behind each transaction, and the '
  'costs each actor carries. Both follow from an instrument designed as an actor inventory '
  'rather than a transaction survey. Section 6.5 sets out the data collection that would '
  'close them.',

 'The four actor categories differ systematically and in the same direction':
  'The four actor categories differ systematically and in the same direction on almost every '
  'characteristic measured. Fishers are younger, schooled to primary level or below, '
  'small-scale, minimally licensed, untrained and un-diversified, and they borrow from the '
  'middlemen who buy from them; middlemen are older, more experienced and better '
  'capitalised; hoteliers and exporters are formally qualified, fully licensed and operating '
  'at a scale upstream actors do not reach. No respondent belonged to a cooperative or a '
  'self-help group. Site mattered for fisher age, marital status and training, but the '
  'larger differences were between actor categories.',

 'The chain runs as a clear functional sequence':
  'The chain runs as a functional sequence from harvesting through aggregation to processing '
  'and export, with the information used to assign value concentrated downstream: fishers '
  'graded on weight alone while every other category used a four-criterion rule, and formal '
  'quality control and contact with the final buyer sat entirely downstream. Reported prices '
  'rose significantly at each node. The fisher retained between 27.5% and 39.6% of the price '
  'the crab eventually fetched, the middleman added between 15.5% and 20.0%, and between '
  '44.4% and 57.0% was added at the final buyer. The first-sale gap was set locally: '
  'Majoreni fishers held 91.7% of the middleman price for large crabs where Shimoni and '
  'Vanga fishers held close to 54%, a difference in what fishers were paid rather than what '
  'traders charged. Price here follows position in the chain, control of the grading rule '
  'and access to alternative buyers, not harvesting effort.',

 'Constraints arise at different points in the chain':
  'Constraints arise at different points and follow the work each actor does: unstable '
  'prices and poor roads for fishers, mortality and inadequate aggregation facilities for '
  'middlemen, seasonality for hoteliers, freight cost and flight risk for exporters. '
  'Barriers to market access were close to universal, no actor had adopted new equipment or '
  'conducted market research, and most respondents regarded the market as poorly structured. '
  'Management-plan awareness reached traders and exporters while missing fishers and '
  'hoteliers. Improvement therefore requires coordinated but actor-specific measures rather '
  'than one intervention applied uniformly.',

 'The South Coast mud crab market is commercially active and institutionally uneven.':
  'The South Coast mud crab market is commercially active and institutionally uneven. '
  'Fishers supply the product with almost no institutional support behind them, while '
  'middlemen and downstream actors hold the grading, the logistics and the connection to '
  'high-value buyers. Site matters for the age of the fishing population, the words used for '
  'grades, the price fishers receive and the constraint middlemen name, but the steadier '
  'divide runs between market nodes rather than between places. Improvement should start '
  'where the terms of exchange are set: a shared grading standard, a reliable public price '
  'record, better live-crab handling, infrastructure aimed at both ends of the chain, '
  'licensing people can obtain, and communication that reaches harvesters as dependably as '
  'it now reaches traders.',

 'Collect transaction-level price, quantity, grade, cost and mortality data':
  'Collect transaction-level price, quantity, grade, cost and mortality data across high and '
  'low seasons so that net marketing margins can be estimated rather than the gross price '
  'spreads reported here. This is the single most important gap in the present study.',

 'Evaluate the price-register, grading-sheet and container pilots':
  'Evaluate the price-register, grading-sheet and container pilots recommended in Section '
  '6.4 with before-and-after measures of price dispersion, mortality and fisher bargaining '
  'outcomes, treating them as interventions to be tested rather than improvements to be '
  'assumed.',
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
missing = [o[:56] for o in REPL if o not in hit]
if missing:
    print('NOT FOUND, nothing saved:')
    for m in missing: print('   ', m)
    raise SystemExit(1)
after = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
json.dump(ch56, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'paragraphs rewritten: {len(hit)}')
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
