# -*- coding: utf-8 -*-
"""The last few hundred words, from the longest remaining paragraphs."""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'Experience accumulated at the trading node rather than the harvesting node,':
  'Experience accumulated at the trading node rather than the harvesting node, which fits '
  'Mirera et al. (2013) on how local knowledge and repeated relationships shape the way crabs '
  'are found, handled and moved, and explains why middlemen reported regular buyers, '
  'competitive price setting and standing agreements while fishers did not. Crona et al. '
  '(2016) describe middlemen in Kenya and Zanzibar as a critical social-ecological link for '
  'that reason, and Cinner et al. (2012) found age and experience shaping how artisanal '
  'fishers met livelihood pressure. Pomeroy and Andrew (2011) argue co-management works best '
  'where local rules are tied to a service users can see.',

 'The site variation in grading language reinforces the point.':
  'The site variation in grading language reinforces the point. At Shimoni 44.0% of fishers '
  'described their large category as mixed and 36.0% did the same for the small category, '
  'while fishers elsewhere used the plain labels, χ²(3, N = 63) = 16.87, p = .001 and χ²(3, N '
  '= 63) = 15.96, p = .002. The survey recorded the label, not a measured carapace width, but '
  'a Shimoni fisher and his buyer may not mean the same thing by large, and that is when a '
  'grading dispute goes the better-informed party’s way.',

 'Reported prices rose at every node, H(3) = 55.84':
  'Reported prices rose at every node, H(3) = 55.84, p < .001 for large crabs and H(3) = '
  '38.00, p < .001 for medium, as expected where later actors carry aggregation, mortality, '
  'transport and buyer-access costs. But these are gross prices: Munga and Muthumbi (2018) '
  'show for the Tana Delta that gross differentials narrow considerably once handling and '
  'transport are netted out. As marketing margins the chain took 60.4% to 72.5% of the final '
  'price, within a structure Table 40 puts at an HHI of 2,371.',

 'The chain runs as a functional sequence':
  'The chain runs as a functional sequence from harvesting through aggregation to processing '
  'and export, with the information used to assign value concentrated downstream: fishers '
  'graded on weight alone while every other category used four criteria, and formal quality '
  'control and contact with the final buyer sat entirely downstream. The fisher retained '
  '27.5% to 39.6% of the price the crab eventually fetched, the middleman added 15.5% to '
  '20.0%, and 44.4% to 57.0% at the final buyer. The first-sale gap was set locally, Majoreni '
  'fishers holding 91.7% of the middleman price for large crabs where Shimoni and Vanga '
  'fishers held close to 54%.',

 'The South Coast mud crab market is commercially active and institutionally uneven.':
  'The South Coast mud crab market is commercially active and institutionally uneven. Fishers '
  'supply the product with almost no institutional support, while middlemen and downstream '
  'actors hold the grading, the logistics and the connection to high-value buyers. Site '
  'matters for fisher age, the words used for grades and the price fishers receive, but the '
  'steadier divide runs between market nodes. Improvement should start where the terms of '
  'exchange are set: a shared grading standard, a public price record, better live-crab '
  'handling, licensing people can obtain, and communication that reaches harvesters.',
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
print(f'paragraphs rewritten: {len(hit)}   saved {before - after}')
