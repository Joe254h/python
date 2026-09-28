# -*- coding: utf-8 -*-
"""The abstract, in one place.

Held separately from fix_abstract.py so the market-structure figures can be
kept in step with the analysis without a second script appending to a
paragraph, which is what pushed it past 600 words.
"""

PARAS = [
 'Mud crab (Scylla serrata) fishing supports coastal livelihoods on the South Coast of Kenya, '
 'yet how the market is organised, and how the value of a crab is shared between the people who '
 'catch, trade and sell it, has not been documented in detail. This study profiled mud crab '
 'actors in Kwale County, examined the functions they perform at each market node, and assessed '
 'the constraints and opportunities each actor category reported. A cross-sectional survey of 96 '
 'respondents — 65 fishers, 22 middlemen, five hoteliers and four exporters — was '
 'carried out between May 2022 and December 2023 using structured questionnaires, field '
 'observation and key-informant interviews. Analysis in IBM SPSS Statistics used valid '
 'percentages within actor category and Beach Management Unit, Monte Carlo chi-square tests based '
 'on 10,000 resamples, Kruskal–Wallis tests for reported prices, and measures of '
 'concentration, marketing margin and price dispersion, at the 5% significance level.',

 'The four actor categories differed systematically. Ninety-five of the 96 respondents were men, '
 'no fisher or middleman had schooling beyond secondary level while every hotelier and exporter '
 'held a certificate, diploma or degree, and no respondent belonged to a cooperative, an '
 'association or a self-help group. Operating licences were held by 12.5% of fishers against '
 'every hotelier and exporter, 93.8% of fishers named a middleman as their main source of credit, '
 'and mean monthly mud crab income rose from KSh 8,969 among fishers to KSh 90,000 among '
 'exporters. Of 68 tests against BMU, nine reached the .05 level; fisher age group was the '
 'clearest, χ²(12, N = 63) = 30.91, p = .004.',

 'Functions divided cleanly by node, and so did the information attached to them. All 65 fishers '
 'graded on weight alone while 95.5% of middlemen and every hotelier and exporter used size, '
 'weight, shell condition and claw size, and formal quality control and contact with the final '
 'buyer sat entirely downstream. Mean large-crab prices rose from KSh 604.6/kg for fishers to '
 'KSh 945.5 for middlemen, KSh 1,700.0 for exporters and KSh 2,200.0 for hoteliers, '
 'H(3) = 55.84, p < .001. First sale was concentrated at every landing site: 63 fishers named '
 'eight buying points between them, a Herfindahl\u2013Hirschman Index of 2,371 overall and 8,580 '
 'at Majoreni, and 76.9% sold to a single buyer. The total gross marketing margin took 60.4% to '
 '72.5% of the final price, leaving the harvester 27.5% to 39.6%, or 24.6% to 35.5% once the '
 '10.4% of landed volume lost to mortality is carried through. Fisher prices differed across '
 'sites, H(3) = 20.32, p < .001, while middleman prices did not, H(2) = 5.33, p = .070, so the '
 'first-sale gap is set locally. Price dispersion fell from a coefficient of variation of 31.8% '
 'among fishers to 6.8% among exporters. No costs were collected, so these are gross margins.',

 'Constraints followed function: price fluctuation and poor roads for fishers, mortality and '
 'missing aggregation facilities for middlemen, seasonality for hoteliers, freight cost and '
 'flight risk for exporters. Barriers to market access were reported by 95.8% of respondents, no '
 'actor had adopted new equipment or conducted market research, and management-plan awareness '
 'reached 95.5% of middlemen but only 15.4% of fishers. The market is commercially active but '
 'institutionally uneven, with grading knowledge, logistics and access to high-value buyers '
 'concentrated downstream. A shared grading standard, a public BMU price register, better '
 'live-crab handling and aggregation facilities, transparent credit terms and practical licensing '
 'support are recommended.',
]

if __name__ == '__main__':
    tot = sum(len(p.split()) for p in PARAS)
    for i, p in enumerate(PARAS, 1):
        print(f'  paragraph {i}: {len(p.split())} words')
    print(f'  total: {tot} words')
