# -*- coding: utf-8 -*-
"""Rewrite the recommendations as prose.

Each one had been set out under four labels, Problem, Evidence, Action and
Expected outcome. The labels made the items long and repetitive, and the
pattern is one the humanizer guidance flags. Each recommendation now runs as
one or two sentences that still name the evidence it rests on, who should act
and what would show it had worked. Every figure is unchanged.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

NEW = {
 '6.4.1 Recommendations From Objective One': [
  'Because only 12.5% of fishers and 27.3% of middlemen held an operating licence against '
  'every hotelier and exporter, the county fisheries department and BMU committees should '
  'run registration and licensing clinics at Shimoni, Majoreni, Vanga and Msambweni, '
  'explaining what a licence costs, what it gives and how to renew it. Success would show '
  'as a rise in upstream licensing at the next survey round.',

  'No fisher used a formal loan, yet 93.8% named a middleman as their main source of '
  'credit and 38.5% were paid at least partly on credit by the same buyer. Financial '
  'institutions, development partners and buyers should separate working capital from the '
  'sale itself, so that a fisher who borrows is not thereby committed to one buyer, and '
  'any advance should carry written terms stating the amount, the repayment and whether '
  'exclusivity applies.',

  'Not one of the 96 respondents belonged to a cooperative, an association or a self-help '
  'group. BMUs and the county should support voluntary groups built around one concrete '
  'service, such as a shared price register, a savings facility or bulk purchase of '
  'containers, since Gutierrez et al. (2011) found that visible benefit, not registration, '
  'is what keeps such groups alive.',

  'Only 7.7% of fishers had received formal training, and training differed significantly '
  'across sites, χ²(3, N = 63) = 8.48, p = .035. Extension officers should deliver '
  'practical BMU-level training in grading, live-crab handling, record keeping and simple '
  'cost calculation, at the landing site rather than at a district centre.',

  'Ninety-five of 96 respondents were men, and the sampling frame drew on landing-site '
  'registers. Future actor mapping by the county and by researchers should deliberately '
  'cover processing, hospitality procurement, retail and crab fattening, where women are '
  'more likely to be found, and should include safeguards for the minors recorded in '
  'harvesting.',
 ],

 '6.4.2 Recommendations From Objective Two': [
  'All 65 fishers graded on weight alone while 95.5% of middlemen and every hotelier and '
  'exporter used size, weight, shell condition and claw size. BMUs, fisheries officers and '
  'buyers should agree a single grading sheet for Grades A, B and C, giving weight ranges '
  'and visible quality criteria, displayed at the point of sale beside the price offered '
  'for each grade and taught with sample crabs. The measure would be working when fewer '
  'than the present 23.1% of fishers record mixed grades for large crabs.',

  'Large-crab and small-crab size labels differed significantly across sites, χ²(3, N = '
  '63) = 16.87, p = .001 and χ²(3, N = 63) = 15.96, p = .002, and 44.0% of Shimoni fishers '
  'used mixed labels. The same grading terms should apply across all four BMUs rather than '
  'being left to local usage.',

  'Every fisher described the price as fixed by the buyer, no actor conducted market '
  'research, and fisher large-crab prices ran from KSh 535.7 at Vanga to KSh 785.7 at '
  'Majoreni. Each BMU should keep a weekly price register by grade, buyer and site, '
  'publishing the median and the observed range rather than a guaranteed price, so that a '
  'fisher has a reference to quote when negotiating.',

  'The fisher retained 27.5% to 39.6% of the end-of-chain price while 44.4% to 57.0% was '
  'added at the final buyer, and first sale was highly concentrated at every landing site. '
  'BMUs and the county should test one direct-supply arrangement between an organised '
  'fisher group and a hotel or exporter, with agreed grades, volumes and payment terms, '
  'and compare the share participants receive against the site baseline recorded here.',

  'Fishers reported 0.5 to 1 kg of daily mortality and 95.5% of middlemen reported 4 to 5 '
  'kg, with no actor keeping records against a common standard. BMUs should pilot '
  'aggregation and live-holding facilities with shade, ventilation, secure reusable '
  'containers, safe loading space and a simple mortality log, and test reusable ventilated '
  'containers against sacks under normal trading conditions.',

  'A hotelier mean of KSh 380.0 per kilogram for medium crabs sits below the fisher price '
  'for the same grade and far below the same respondents’ large-crab mean of KSh '
  '2,200.0. Those five records should be checked against the original questionnaires and '
  'field notes to confirm unit, product form and transaction context before any '
  'value-addition estimate uses them.',
 ],

 '6.4.3 Recommendations From Objective Three': [
  'Poor roads were named by 98.5% of fishers and the lack of aggregation facilities by '
  '90.9% of middlemen, so the county should prepare one infrastructure plan in which each '
  'investment names the actor it serves: access routes and landing facilities for fishers, '
  'aggregation and holding facilities for middlemen, demand coordination for hotels and '
  'freight-risk planning for exporters.',

  'Management-plan awareness reached 95.5% of middlemen and every exporter but only 15.4% '
  'of fishers and no hotelier. BMUs and fisheries officers should aim that communication '
  'at fishers and hoteliers first, record who received it and check understanding rather '
  'than counting attendance.',

  'Price fluctuation was the main constraint for 90.8% of fishers and half the middlemen, '
  'while 95.5% of middlemen named price stability as their priority. County and national '
  'agencies should work on stability through reliable information, consistent grading, '
  'predictable payment terms and buyer competition rather than a guaranteed price, which '
  'these data do not support and which no institution in the chain could enforce.',

  'Diversification was the only risk-management method fishers, middlemen and hoteliers '
  'named, yet no respondent had adopted an innovative response. Development partners and '
  'the county should run small costed pilots such as crab fattening, each tied to a '
  'confirmed buyer, reporting survival, feed and labour costs and a realised price so the '
  'next round can be judged on evidence.',

  'Every respondent expressing a view rated youth involvement low or very low, yet 53.8% '
  'of fishers were aged 18 to 35 and four were under 18. County youth and fisheries '
  'programmes should combine technical training with supervised market access, savings or '
  'credit and mentorship, define youth participation explicitly in any monitoring tool and '
  'include safeguards for minors.',
 ],
}

out, cur, dropped = [], None, {}
for b in ch56:
    if b['k'] in ('h1', 'h2', 'h3'):
        cur = b['t']
        out.append(b)
        if cur in NEW:
            for i, t in enumerate(NEW[cur]):
                out.append({'k': 'num', 't': t, 'ref': b.get('ref', 'n1')})
            dropped[cur] = 0
        continue
    if cur in NEW and b['k'] in ('p', 'num', 'bul'):
        dropped[cur] += 1
        continue
    out.append(b)

# carry the original list reference so numbering still renders
refs = {}
for b in ch56:
    if b['k'] == 'num' and b.get('ref'):
        refs.setdefault('last', b['ref'])
for b in out:
    if b['k'] == 'num' and not b.get('ref'):
        b['ref'] = refs.get('last', 'n1')

before = sum(len(b['t'].split()) for b in ch56 if b['k'] in ('p', 'bul', 'num'))
after = sum(len(b['t'].split()) for b in out if b['k'] in ('p', 'bul', 'num'))
json.dump(out, open(P, 'w'), ensure_ascii=False, indent=1)
for k, v in dropped.items():
    print(f'  {k[:46]:48s} {v} items -> {len(NEW[k])}')
print(f'\nChapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
