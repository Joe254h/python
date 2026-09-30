# -*- coding: utf-8 -*-
"""Final pass over Chapter Five.

The three "Key Findings" subsections restated what Chapter Four's summaries
already give, three chapters running, so they go and each objective's
discussion opens on the comparison instead. The longest remaining paragraphs
are tightened. Every citation, figure and test statistic is kept, and the
Implications subsections stay, since they carry the theoretical and practical
reading the discussion exists for.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

DROP_SECTIONS = {'5.2.1 Key Findings', '5.3.1 Key Findings', '5.4.1 Key Findings'}

REPL = {
 'Experience accumulated at the trading node rather than the harvesting node,':
  'Experience accumulated at the trading node rather than the harvesting node, which fits '
  'Mirera et al. (2013) on how local knowledge and repeated relationships shape the way crabs '
  'are found, handled and moved, and explains why middlemen reported regular buyers, '
  'competitive price setting and standing agreements while fishers did not. Crona et al. '
  '(2016) describe middlemen in Kenya and Zanzibar as a critical social-ecological link for '
  'that reason, and Cinner et al. (2012) found age and experience shaping how artisanal '
  'fishers responded to livelihood pressure. Licensing showed the same upstream weakness, and '
  'Pomeroy and Andrew (2011) argue co-management works best where local rules are tied to a '
  'service users can see.',

 'Reported prices rose at every node and the actor comparisons were unambiguous,':
  'Reported prices rose at every node, H(3) = 55.84, p < .001 for large crabs and H(3) = '
  '38.00, p < .001 for medium, as expected where later actors carry aggregation, mortality, '
  'transport and buyer-access costs. But these are gross prices: Munga and Muthumbi (2018) '
  'show for the Tana Delta that gross differentials narrow considerably once handling and '
  'transport are netted out. As marketing margins, the chain took 60.4% to 72.5% of the final '
  'price before it reached the harvester, within a structure Table 40 puts at an HHI of 2,371 '
  'with 76.9% of harvesters dealing with a single buyer.',

 'A large crab reaching an exporter left 35.6% with the fisher,':
  'A large crab reaching an exporter left 35.6% with the fisher, 20.0% at the middleman step '
  'and 44.4% at the exporter step; one reaching a hotel kitchen left the fisher 27.5% and the '
  'hotel 57.0%; medium crabs for export were the fisher’s best case at 39.6%. Jacinto (2004) '
  'argues the share captured at each node tracks control of information and market access '
  'more closely than physical effort, which is the ordering here.',

 'The middleman result cuts against the usual account:':
  'The middleman result cuts against the usual account: middlemen took the smallest of the '
  'three shares, between 15.5% and 20.0%, yet fishers most often identify them with the low '
  'beach price. Crona et al. (2016) reach the same conclusion for Kenya and Zanzibar, finding '
  'middlemen carrying the mortality risk, which Chapter Four documents at 4 to 5 kg a day '
  'against 0.5 to 1 kg among fishers.',

 'The actor and site comparisons answer different questions,':
  'The actor and site comparisons answer different questions: compare sites without holding '
  'the actor constant and a site with more middlemen looks like a high-price site through its '
  'respondent mix alone. With the role held constant, fisher prices differed significantly '
  'across sites for large crabs, H(3) = 20.32, p < .001, and medium, H(3) = 20.07, p < .001, '
  'while middleman prices did not, H(2) = 5.33, p = .070 and H(2) = 3.78, p = .151.',

 'That asymmetry produced the study’s sharpest contrast.':
  'That asymmetry produced the sharpest contrast in the study. At Majoreni the fisher price '
  'stood at 91.7% of the local middleman price for large crabs and 91.3% for medium; at '
  'Shimoni and Vanga the same figures were 55.0% and 53.6%. The narrow Majoreni gap is built '
  'on the fisher side: its traders sold at KSh 857.1, within KSh 143 of the other two sites, '
  'while its fishers were paid KSh 785.7 against roughly KSh 537 elsewhere.',

 'Two readings fit.':
  'Two readings fit. Majoreni fishers may face a less concentrated set of first buyers, so '
  'competition at the beach lifts the price; or the seven middlemen sampled there may be '
  'first-tier buyers reselling locally rather than consolidators, making the comparison not '
  'quite like for like. This study cannot separate them. Green and Clark (2021) treat '
  'dispersion at first sale as a reliable indicator of weak integration, and on that '
  'criterion Shimoni and Vanga look the weaker markets.',

 'Concentration is measured over harvesters rather than volume,':
  'Concentration is measured over harvesters rather than volume, because a textbook ratio '
  'needs a census of buyers and the quantity each handles. Table 40 weights buying points by '
  'the share of harvesters attached to each: an HHI of 2,371 across the four BMUs and 8,580 '
  'at Majoreni, where a numbers-equivalent of 1.17 outlets means one buying point in '
  'practice, putting every BMU above the 2,500 mark conventionally treated as high '
  'concentration.',

 'The sample was not fully probabilistic.':
  'The sample was not fully probabilistic. Reliable lists were unavailable downstream, so '
  'referral and convenience procedures were used and the findings describe the respondents '
  'reached. The achieved fisher sample of 65 fell short of the calculated 83, 78.3%, and only '
  'five hoteliers and four exporters were sampled, with no middleman at Msambweni and only '
  'three fishers there.',

 'The design was cross-sectional over a single survey period,':
  'The design was cross-sectional over a single survey period, so seasonal variation is not '
  'captured and no causal direction established, and prices, income and losses were '
  'self-reported. Sixty-eight categorical tests ran without a correction for multiple '
  'comparisons, so associations close to .05 are exploratory. What remains genuinely '
  'unmeasured is the volume behind each transaction and the costs each actor carries, both '
  'following from an instrument designed as an actor inventory. Section 6.5 sets out the data '
  'collection that would close them.',

 'The profile results support treating actor category rather than location':
  'The profile results support treating actor category rather than location as the primary '
  'structural variable here, and identify three entry points needing no new infrastructure: a '
  'licensing route upstream actors can complete, a source of working capital that is not the '
  'buyer, and a collective body with a service attached.',

 'These results locate the mechanism of value capture':
  'These results locate the mechanism of value capture in control of the grading rule and of '
  'the connection to the final buyer, rather than in harvesting effort or the middleman’s '
  'margin. Two interventions follow and neither needs capital: a written grading standard '
  'both parties to a first sale can read, and an independent record of what grades are '
  'fetching.',
}

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
out, cur, dropped = [], None, 0
for b in ch56:
    if b.get('k') in ('h1', 'h2', 'h3', 'h4'):
        cur = b['t']
        if cur in DROP_SECTIONS:
            dropped += 1
            continue
        out.append(b); continue
    if cur in DROP_SECTIONS:
        continue
    out.append(b)

hit = set()
for b in out:
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
after = sum(len(b['t'].split()) for b in out if b.get('k') in ('p', 'bul', 'num'))
json.dump(out, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'Key Findings subsections removed: {dropped}   paragraphs rewritten: {len(hit)}')
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
