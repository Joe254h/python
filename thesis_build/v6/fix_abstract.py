# -*- coding: utf-8 -*-
"""Rewrite the abstract so it matches the rebuilt results: four-actor tables,
the Kruskal-Wallis price comparisons and the value-distribution finding."""
import docx, copy
from docx.oxml.ns import qn
DOC = 'v6/thesis.docx'
d = docx.Document(DOC)
ps = d.paragraphs
i = next(k for k, p in enumerate(ps) if p.text.strip() == 'ABSTRACT')
target = None
for p in ps[i:i + 6]:
    if p.text.strip().startswith('Mud crab (Scylla serrata) fishing supports'):
        target = p; break
assert target is not None, 'abstract paragraph not found'

# drop any abstract paragraphs a previous run inserted, so this is idempotent
ti = next(k for k, p in enumerate(ps) if p._p is target._p)
while True:
    ps = d.paragraphs
    ti = next(k for k, p in enumerate(ps) if p._p is target._p)
    if ti + 1 >= len(ps):
        break
    nxt = ps[ti + 1].text.strip()
    if not nxt or nxt.startswith(('TABLE OF CONTENTS', 'DECLARATION', 'LIST OF')):
        break
    ps[ti + 1]._p.getparent().remove(ps[ti + 1]._p)

PARAS = [
 'Mud crab (Scylla serrata) fishing supports coastal livelihoods on the South Coast of Kenya, yet '
 'how the market is organised, and how the value of a crab is shared between the people who catch, '
 'trade and sell it, has not been documented in detail. This study profiled mud crab actors in '
 'Kwale County, examined the functions they perform at each market node, and assessed the '
 'constraints and opportunities each actor category reported. A cross-sectional survey of 96 '
 'respondents \u2014 65 fishers, 22 middlemen, five hoteliers and four exporters \u2014 was carried out '
 'between May 2022 and December 2023 using structured questionnaires, field observations and '
 'key-informant interviews. Analysis in IBM SPSS Statistics used valid percentages within actor '
 'category and Beach Management Unit, descriptive statistics for income and prices, Monte Carlo '
 'chi-square tests based on 10,000 resamples for associations with BMU among fishers and '
 'middlemen, and Kruskal\u2013Wallis tests for reported prices, at the 5% significance level. '
 'Every table reports all four actor categories.',

 'The four actor categories differed systematically. Ninety-five of the 96 respondents were men. '
 'No fisher or middleman had schooling beyond secondary level while every hotelier and exporter '
 'held a certificate, diploma or degree, and no respondent in any category belonged to a '
 'cooperative, an association or a self-help group. Operating licences were held by 12.5% of '
 'fishers against every hotelier and exporter, 93.8% of fishers named a middleman as their main '
 'source of credit, and mean monthly mud crab income rose from KSh 8,969 among fishers to '
 'KSh 90,000 among exporters. Of 68 tests against BMU, nine reached the .05 level; fisher age '
 'group was the clearest, \u03c7\u00b2(12, N = 63) = 30.91, p = .004.',

 'Functions divided cleanly by node and so did the information attached to them. All 65 fishers '
 'graded on weight alone while 95.5% of middlemen and every hotelier and exporter used size, '
 'weight, shell condition and claw size; formal quality control and contact with the final buyer '
 'sat entirely downstream. Mean large-crab prices were KSh 604.6/kg for fishers, KSh 945.5/kg for '
 'middlemen, KSh 1,700.0/kg for exporters and KSh 2,200.0/kg for hoteliers, H(3) = 55.84, '
 'p < .001. Expressed as shares of the end-of-chain price, the fisher retained 27.5% to 39.6%, the '
 'middleman added 15.5% to 20.0%, and 44.4% to 57.0% was added at the final buyer. Fisher prices '
 'differed across sites, H(3) = 20.32, p < .001, while middleman prices did not, H(2) = 5.33, '
 'p = .070, so the first-sale gap was set locally: Majoreni fishers held 91.7% of the local '
 'middleman price against close to 54% at Shimoni and Vanga. Since no cost data were collected '
 'these are gross price spreads, not net margins.',

 'Constraints followed function: price fluctuation and poor roads for fishers, mortality and '
 'missing aggregation facilities for middlemen, seasonality for hoteliers, freight cost and flight '
 'risk for exporters. Barriers to market access were reported by 95.8% of respondents, no actor '
 'had adopted new equipment or conducted market research, and management-plan awareness reached '
 '95.5% of middlemen but only 15.4% of fishers. The market is commercially active but '
 'institutionally uneven, with grading knowledge, logistics and access to high-value buyers '
 'concentrated downstream. A shared grading standard, a public BMU price register, better '
 'live-crab handling and aggregation facilities, transparent credit terms and practical licensing '
 'support are recommended.',
]

# first paragraph reuses the existing one; the rest are deep copies of it
target.runs[0].text = PARAS[0]
for r in target.runs[1:]:
    r.text = ''
prev = target._p
for text in PARAS[1:]:
    el = copy.deepcopy(target._p)
    first = None
    for t in el.iter(qn('w:t')):
        if first is None:
            first = t; t.text = text; t.set(qn('xml:space'), 'preserve')
        else:
            t.text = ''
    prev.addnext(el)
    prev = el
d.save(DOC)

d2 = docx.Document(DOC)
ps = d2.paragraphs
i = next(k for k, p in enumerate(ps) if p.text.strip() == 'ABSTRACT')
tot = 0
for p in ps[i + 1:i + 7]:
    t = p.text.strip()
    if not t or t == 'TABLE OF CONTENTS':
        continue
    print(f'[{len(t.split())} words] {t[:96]}...')
    tot += len(t.split())
print('abstract total:', tot, 'words')
