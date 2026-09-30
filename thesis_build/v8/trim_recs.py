# -*- coding: utf-8 -*-
"""Tighten the sixteen recommendations.

Each still names the evidence it rests on and who should act. What goes is the
formulaic success-criterion clause on the ones that had it, and the repeated
naming of the four sites and the four actor categories.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'Because only 12.5% of fishers and 27.3% of middlemen held an operating licence':
  'Only 12.5% of fishers and 27.3% of middlemen held an operating licence, against every '
  'hotelier and exporter. The county fisheries department and BMU committees should run '
  'registration and licensing clinics at all four sites, explaining what a licence costs, '
  'what it gives and how to renew it.',

 'No fisher used a formal loan, yet 93.8% named a middleman':
  'No fisher used a formal loan, yet 93.8% named a middleman as their main credit source and '
  '38.5% were paid at least partly on credit by the same buyer. Financial institutions, '
  'development partners and buyers should separate working capital from the sale itself, so '
  'a fisher who borrows is not committed to one buyer, and any advance should carry written '
  'terms stating amount, repayment and whether exclusivity applies.',

 'Not one of the 96 respondents belonged to a cooperative':
  'Not one of the 96 respondents belonged to a cooperative, an association or a self-help '
  'group. BMUs and the county should support voluntary groups built around one concrete '
  'service, such as a shared price register, a savings facility or bulk purchase of '
  'containers, since Gutierrez et al. (2011) found visible benefit, not registration, keeps '
  'such groups alive.',

 'Only 7.7% of fishers had received formal training':
  'Only 7.7% of fishers had received formal training, and training differed significantly '
  'across sites, χ²(3, N = 63) = 8.48, p = .035. Extension officers should deliver '
  'practical training in grading, live-crab handling, record keeping and simple cost '
  'calculation at the landing site rather than at a district centre.',

 'Ninety-five of 96 respondents were men, and the sampling frame':
  'Ninety-five of 96 respondents were men, and the sampling frame drew on landing-site '
  'registers. Future actor mapping should deliberately cover processing, hospitality '
  'procurement, retail and crab fattening, where women are more likely to be found, and '
  'should include safeguards for the minors recorded in harvesting.',

 'All 65 fishers graded on weight alone while 95.5% of middlemen':
  'All 65 fishers graded on weight alone while 95.5% of middlemen and every hotelier and '
  'exporter used size, weight, shell condition and claw size. BMUs, fisheries officers and '
  'buyers should agree a single grading sheet for Grades A, B and C, giving weight ranges and '
  'visible quality criteria, displayed at the point of sale beside the price offered for each '
  'grade. It would be working when fewer than the present 23.1% of fishers record mixed '
  'grades for large crabs.',

 'Large-crab and small-crab size labels differed significantly across sites':
  'Large-crab and small-crab size labels differed significantly across sites, χ²(3, N = 63) '
  '= 16.87, p = .001 and χ²(3, N = 63) = 15.96, p = .002, and 44.0% of Shimoni fishers used '
  'mixed labels. The same grading terms should apply across all four BMUs rather than being '
  'left to local usage.',

 'Every fisher described the price as fixed by the buyer':
  'Every fisher described the price as fixed by the buyer, no actor conducted market '
  'research, and fisher large-crab prices ran from KSh 535.7 at Vanga to KSh 785.7 at '
  'Majoreni. Each BMU should keep a weekly price register by grade, buyer and site, '
  'publishing the median and the observed range rather than a guaranteed price, so a fisher '
  'has a reference to quote.',

 'The fisher retained 27.5% to 39.6% of the end-of-chain price':
  'The fisher retained 27.5% to 39.6% of the end-of-chain price while 44.4% to 57.0% was '
  'added at the final buyer, and first sale was concentrated at every landing site. BMUs and '
  'the county should test one direct-supply arrangement between an organised fisher group '
  'and a hotel or exporter, with agreed grades, volumes and payment terms, and compare the '
  'share participants receive against the site baseline recorded here.',

 'Fishers reported 0.5 to 1 kg of daily mortality':
  'Fishers reported 0.5 to 1 kg of daily mortality and 95.5% of middlemen reported 4 to 5 '
  'kg, with no actor keeping records against a common standard. BMUs should pilot '
  'aggregation and live-holding facilities with shade, ventilation, secure reusable '
  'containers, safe loading space and a mortality log, and test reusable ventilated '
  'containers against sacks in normal trading.',

 'A hotelier mean of KSh 380.0 per kilogram for medium crabs':
  'A hotelier mean of KSh 380.0 per kilogram for medium crabs sits below the fisher price '
  'for the same grade and far below the same respondents’ large-crab mean of KSh 2,200.0. '
  'Those five records should be checked against the original questionnaires to confirm unit, '
  'product form and transaction context before any value-addition estimate uses them.',

 'Poor roads were named by 98.5% of fishers':
  'Poor roads were named by 98.5% of fishers and the lack of aggregation facilities by 90.9% '
  'of middlemen, so the county should prepare one infrastructure plan in which each '
  'investment names the actor it serves: access routes and landing facilities for fishers, '
  'aggregation and holding facilities for middlemen, demand coordination for hotels, '
  'freight-risk planning for exporters.',

 'Management-plan awareness reached 95.5% of middlemen':
  'Management-plan awareness reached 95.5% of middlemen and every exporter but only 15.4% of '
  'fishers and no hotelier. BMUs and fisheries officers should aim that communication at '
  'fishers and hoteliers first, record who received it and check understanding rather than '
  'counting attendance.',

 'Price fluctuation was the main constraint for 90.8% of fishers':
  'Price fluctuation was the main constraint for 90.8% of fishers and half the middlemen, '
  'while 95.5% of middlemen named price stability as their priority. County and national '
  'agencies should work on stability through reliable information, consistent grading, '
  'predictable payment terms and buyer competition rather than a guaranteed price, which '
  'these data do not support and no institution here could enforce.',

 'Diversification was the only risk-management method':
  'Diversification was the only risk-management method fishers, middlemen and hoteliers '
  'named, yet no respondent had adopted an innovative response. Development partners and the '
  'county should run small costed pilots such as crab fattening, each tied to a confirmed '
  'buyer, reporting survival, feed and labour costs and a realised price.',

 'Every respondent expressing a view rated youth involvement low':
  'Every respondent expressing a view rated youth involvement low or very low, yet 53.8% of '
  'fishers were aged 18 to 35 and four were under 18. County youth and fisheries programmes '
  'should combine technical training with supervised market access, savings or credit and '
  'mentorship, define youth participation explicitly in any monitoring tool and include '
  'safeguards for minors.',
}

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
hit = set()
for b in ch56:
    if b.get('k') != 'num':
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
print(f'recommendations rewritten: {len(hit)}')
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
