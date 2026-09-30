# -*- coding: utf-8 -*-
"""The abstract, in one place.

Structured so a reader meets every part of the thesis in order: background,
the problem, the framework, the method, the findings, what they mean, the
conclusion and the recommendations.
"""

PARAS = [
 # background, problem, framework, objectives
 'Mud crab (Scylla serrata) fishing supports coastal livelihoods on the South Coast of '
 'Kenya, and demand from hotels and export buyers has raised its commercial value. How the '
 'market is organised, and how the value of a crab is shared between the people who catch, '
 'trade and sell it, has not been documented for Kwale County, so management has had little '
 'basis for judging who carries the risk and who captures the return. Guided by the '
 'structure-conduct-performance framework, with value-chain and livelihood concepts in a '
 'supporting role, this study profiled the actors, examined the functions they perform at '
 'each market node, and assessed the constraints and opportunities each category reported.',

 # methodology
 'A cross-sectional survey covered 96 respondents, 65 fishers, 22 middlemen, five hoteliers '
 'and four exporters, at Shimoni, Majoreni, Vanga and Msambweni between May 2022 and '
 'December 2023, using structured questionnaires, field observation and key-informant '
 'interviews. Analysis in IBM SPSS Statistics used valid percentages within actor category '
 'and Beach Management Unit, Monte Carlo chi-square tests on 10,000 resamples, '
 'Kruskal-Wallis tests for reported prices, and measures of concentration, marketing margin '
 'and price dispersion, at the 5% significance level.',

 # findings
 'The four categories differed in the same direction on almost every measure. Ninety-five of '
 '96 respondents were men, no fisher or middleman had schooling beyond secondary level, and '
 'no respondent belonged to a cooperative or self-help group; 12.5% of fishers held a licence '
 'against every hotelier and exporter, and 93.8% named a middleman as their main source of '
 'credit. Mean monthly income rose from KSh 8,969 among fishers to KSh 90,000 among '
 'exporters. All 65 fishers graded on weight alone while 95.5% of middlemen and every '
 'hotelier and exporter used four criteria. Mean large-crab prices rose from KSh 604.6/kg for '
 'fishers to KSh 945.5 for middlemen, KSh 1,700.0 for exporters and KSh 2,200.0 for '
 'hoteliers, H(3) = 55.84, p < .001. First sale was concentrated at every landing site, with '
 'a Herfindahl-Hirschman Index of 2,371 overall and 8,580 at Majoreni, and 76.9% of fishers '
 'sold to a single buyer. The total gross marketing margin took 60.4% to 72.5% of the final '
 'price, and price dispersion fell from a coefficient of variation of 31.8% among fishers to '
 '6.8% among exporters.',

 # discussion and conclusion
 'Many unorganised sellers face few buyers, the buyer controls both the grading rule and the '
 'price, and credit ties the seller to that buyer, so the harvester keeps the smallest share '
 'of a price set furthest from the water. Since no costs were collected these are gross '
 'margins and not profits. The market is commercially active but institutionally uneven, with '
 'grading knowledge, logistics and access to high-value buyers held downstream, and the '
 'binding constraint on fisher earnings is the terms of exchange rather than the volume '
 'landed.',

 # recommendations
 'Beach Management Units and county fisheries officers should publish a weekly price register '
 'by grade and buyer and adopt a shared grade sheet using weight and visible shell condition. '
 'County government and development partners should prioritise feeder access and shaded '
 'live-holding points to cut handling loss, buyers and lenders should record short written '
 'credit terms, and fisheries officers should run licensing and training clinics at the '
 'landing site. Further research should follow single consignments through the chain with '
 'costs and volumes attached.',
]

if __name__ == '__main__':
    tot = 0
    for i, p in enumerate(PARAS, 1):
        w = len(p.split()); tot += w
        print(f'  paragraph {i}: {w:3d} words')
    print(f'  total: {tot} words')
