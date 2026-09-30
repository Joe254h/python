# -*- coding: utf-8 -*-
"""Shorten the recommendations and the further-research list.

Each keeps the evidence it rests on and the body that should act. What goes is
the second clause explaining what the measure would achieve, which repeats the
finding it came from.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'Only 12.5% of fishers and 27.3% of middlemen held an operating licence':
  'Only 12.5% of fishers and 27.3% of middlemen held an operating licence, against every '
  'hotelier and exporter. The county fisheries department and BMU committees should run '
  'registration and licensing clinics at all four sites, explaining what a licence costs, '
  'gives and how to renew it.',

 'No fisher used a formal loan, yet 93.8% named a middleman as their main credit source':
  'No fisher used a formal loan, yet 93.8% named a middleman as their main credit source. '
  'Financial institutions, development partners and buyers should separate working capital '
  'from the sale itself, and any advance should carry written terms stating amount, repayment '
  'and whether exclusivity applies.',

 'Not one of the 96 respondents belonged to a cooperative':
  'Not one of the 96 respondents belonged to a cooperative, an association or a self-help '
  'group. BMUs and the county should support voluntary groups built around one concrete '
  'service, since Gutierrez et al. (2011) found visible benefit, not registration, keeps such '
  'groups alive.',

 'Only 7.7% of fishers had received formal training':
  'Only 7.7% of fishers had received formal training, and training differed significantly '
  'across sites, χ²(3, N = 63) = 8.48, p = .035. Extension officers should deliver training '
  'in grading, live-crab handling, record keeping and cost calculation at the landing site.',

 'Ninety-five of 96 respondents were men':
  'Ninety-five of 96 respondents were men and the frame drew on landing-site registers. '
  'Future actor mapping should cover processing, hospitality procurement, retail and crab '
  'fattening, where women are more likely to be found, with safeguards for the minors '
  'recorded in harvesting.',

 'All 65 fishers graded on weight alone while 95.5% of middlemen':
  'All 65 fishers graded on weight alone while 95.5% of middlemen and every hotelier and '
  'exporter used four criteria. BMUs, fisheries officers and buyers should agree a single '
  'grading sheet for Grades A, B and C, giving weight ranges and visible quality criteria, '
  'displayed at the point of sale beside the price offered for each grade.',

 'Large-crab and small-crab size labels differed significantly across sites':
  'Large-crab and small-crab size labels differed significantly across sites, χ²(3, N = 63) '
  '= 16.87, p = .001 and χ²(3, N = 63) = 15.96, p = .002. The same grading terms should apply '
  'across all four BMUs rather than being left to local usage.',

 'Every fisher described the price as fixed by the buyer':
  'Every fisher described the price as fixed by the buyer, no actor conducted market '
  'research, and fisher large-crab prices ran from KSh 535.7 at Vanga to KSh 785.7 at '
  'Majoreni. Each BMU should keep a weekly price register by grade, buyer and site, '
  'publishing the median and the observed range rather than a guaranteed price.',

 'The fisher retained 27.5% to 39.6% of the end-of-chain price':
  'The fisher retained 27.5% to 39.6% of the end-of-chain price while 44.4% to 57.0% was '
  'added at the final buyer. BMUs and the county should test one direct-supply arrangement '
  'between an organised fisher group and a hotel or exporter, with agreed grades, volumes and '
  'payment terms, against the site baseline recorded here.',

 'Fishers reported 0.5 to 1 kg of daily mortality':
  'Fishers reported 0.5 to 1 kg of daily mortality and 95.5% of middlemen 4 to 5 kg, with no '
  'actor keeping records against a common standard. BMUs should pilot aggregation and '
  'live-holding facilities with shade, ventilation, secure reusable containers and a '
  'mortality log.',

 'A hotelier mean of KSh 380.0 per kilogram for medium crabs':
  'A hotelier mean of KSh 380.0 per kilogram for medium crabs sits below the fisher price for '
  'the same grade. Those five records should be checked against the original questionnaires '
  'to confirm unit, product form and transaction context before any value-addition estimate '
  'uses them.',

 'Poor roads were named by 98.5% of fishers':
  'Poor roads were named by 98.5% of fishers and the lack of aggregation facilities by 90.9% '
  'of middlemen. The county should prepare one infrastructure plan in which each investment '
  'names the actor it serves: access routes for fishers, holding facilities for middlemen, '
  'demand coordination for hotels, freight planning for exporters.',

 'Management-plan awareness reached 95.5% of middlemen':
  'Management-plan awareness reached 95.5% of middlemen and every exporter but only 15.4% of '
  'fishers and no hotelier. BMUs and fisheries officers should aim that communication at '
  'fishers and hoteliers first, recording who received it and checking understanding.',

 'Price fluctuation was the main constraint for 90.8% of fishers':
  'Price fluctuation was the main constraint for 90.8% of fishers while 95.5% of middlemen '
  'named price stability as their priority. County and national agencies should work on '
  'stability through reliable information, consistent grading, predictable payment terms and '
  'buyer competition rather than a guaranteed price.',

 'Diversification was the only risk-management method':
  'Diversification was the only risk-management method fishers, middlemen and hoteliers '
  'named, and no respondent had adopted an innovative response. Development partners and the '
  'county should run small costed pilots such as crab fattening, each tied to a confirmed '
  'buyer.',

 'Every respondent expressing a view rated youth involvement low':
  'Every respondent expressing a view rated youth involvement low or very low, yet 53.8% of '
  'fishers were aged 18 to 35 and four were under 18. County youth and fisheries programmes '
  'should combine technical training with supervised market access, credit and mentorship, '
  'and include safeguards for minors.',

 # ---- 6.5 further research
 'Collect transaction-level price, quantity, grade, cost and mortality data':
  'Collect transaction-level price, quantity, grade, cost and mortality data across high and '
  'low seasons so that net marketing margins can be estimated rather than gross price '
  'spreads. This is the single most important gap in the present study.',

 'Repeat the survey with probability sampling':
  'Repeat the survey with probability sampling wherever reliable actor lists can be built, '
  'ensuring each target BMU contributes both fisher and middleman observations.',

 'Oversample hoteliers, exporters, women and young people':
  'Oversample hoteliers, exporters, women and young people so that downstream functions and '
  'under-represented participants can be analysed with precision this sample does not allow.',

 'Measure buyer concentration and onward destination at transaction level':
  'Measure buyer concentration and onward destination at transaction level, which would '
  'separate the two explanations offered here for the narrow first-sale gap at Majoreni.',

 'Use qualitative interviews to clarify buyer advances':
  'Use qualitative interviews to clarify buyer advances, loan terms, tied-supply '
  'relationships and grading disputes.',

 'Evaluate the price-register, grading-sheet and container pilots':
  'Evaluate the price-register, grading-sheet and container pilots recommended in Section 6.4 '
  'with before-and-after measures of price dispersion, mortality and fisher bargaining '
  'outcomes.',
}

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
hit = set()
for b in ch56:
    if b.get('k') not in ('num', 'bul', 'p'):
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
print(f'list items rewritten: {len(hit)}')
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
