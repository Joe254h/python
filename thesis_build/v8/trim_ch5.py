# -*- coding: utf-8 -*-
"""Tighten the four heaviest discussion sections in Chapter Five.

Every citation, figure and test statistic is kept. What goes is the framing:
sentences that announce what the next sentence will do, and qualifications
already made in the same paragraph.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

NEW = {
 '5.2.2 Gender and the Limits of the Sampling Frame': [
  'Ninety-five of the 96 respondents were men, and the one woman was a hotelier rather than '
  'a harvester. That matches what has been reported along the Kenyan coast, where '
  'harvesting and much of the first-tier trade are male-dominated while women appear more '
  'often in processing, retail and culture activities (Mirera, 2014a; Ochiewo et al., 2010).',

  'Why men dominate harvesting here is not something these data can settle, but three '
  'mechanisms in the literature fit the setting. Harvesting is done on foot in mangrove '
  'creeks at low spring tides, often at night and at a distance from the village, which '
  'carries mobility and safety costs that fall unequally on women (Mirera et al., 2013; '
  'Moser et al., 2005). Landing-site registers and BMU membership, the routes by which a '
  'harvester becomes visible to officials and buyers, have historically enrolled men. And '
  'the credit relationship documented in Chapter Four runs through established trading ties '
  'that new entrants do not have.',

  'The consequence is methodological before it is substantive. Because the fisher sampling '
  'frame drew on landing-site registers, women working in processing, hospitality '
  'procurement, retail or crab fattening were unlikely to be reached. Ndanga et al. (2013) '
  'show that women in Kenyan aquaculture value chains concentrate in exactly the nodes '
  'landing-site sampling does not cover, which is both a plausible explanation for the '
  'pattern here and a brief for future work. The finding describes the respondents reached, '
  'not an absence of women from the chain. Hospitality procurement and crab fattening are '
  'the two openings, and respondents named both as opportunities.',
 ],

 '5.2.3 Experience, Licensing and the Absence of Collective Organisation': [
  'Experience accumulated at the trading node rather than the harvesting node. This fits '
  'Mirera et al. (2013), where local knowledge and repeated relationships shape how crabs '
  'are found, handled and moved, and it helps explain why middlemen reported regular '
  'buyers, competitive price setting and standing trading agreements while fishers did not. '
  'Crona et al. (2016) describe middlemen in Kenya and Zanzibar as a critical '
  'social-ecological link precisely because that relational knowledge is not easily '
  'replaced, and Cinner et al. (2012) found age and accumulated experience shaping how '
  'artisanal fishers responded to livelihood pressure, which fits the age gap recorded here '
  'between the two nodes. Licensing showed the same upstream weakness: a small share of '
  'fishers and middlemen held one, against every hotelier and exporter. Pomeroy and Andrew '
  '(2011) argue that co-management works best where local rules are tied to a service users '
  'can see, which points to licensing support delivered through the BMUs rather than '
  'enforcement alone.',

  'The complete absence of collective membership matters more than a single percentage '
  'suggests. Groups are the normal vehicle for price information, savings, training, '
  'traceability and dealings with government, and the literature ties organised groups and '
  'local leadership to better fishery outcomes (Gutiérrez et al., 2011; Mirera, 2014a). '
  'Without one, a fisher negotiates alone against a buyer with twenty years in the trade '
  'who knows what crabs fetch further up the chain.',

  'Forming groups is not itself the remedy. Gutiérrez et al. (2011) found that leadership '
  'and clear incentives, not the existence of a group, separate the successful cases. That '
  'nothing exists here at any node suggests earlier attempts offered members nothing they '
  'could see. Any group formed in response to this study would need a commercial purpose, '
  'transparent leadership and a service members can point to.',
 ],

 '5.3.4 Price Formation and the Distribution of Value': [
  'Reported prices rose at every node and the actor comparisons were unambiguous, H(3) = '
  '55.84, p < .001 for large crabs and H(3) = 38.00, p < .001 for medium. Rising prices are '
  'expected where later actors carry aggregation, mortality, transport, packaging and '
  'buyer-access costs, but these are gross prices. Munga and Muthumbi (2018) draw the same '
  'distinction for the Tana Delta, where gross differentials narrowed considerably once '
  'handling and transport were netted out, so nothing here is a statement about profit. '
  'Expressed as marketing margins, the chain took between 60.4% and 72.5% of the final '
  'price before it reached the harvester, and the concentration figures in Table 40 '
  'describe the structure within which that split is settled: an HHI of 2,371 across the '
  'four BMUs, and 76.9% of harvesters dealing with a single buyer.',

  'Within that limit, each node’s price as a share of the end-of-chain price answers how '
  'value is distributed. A large crab reaching an exporter left 35.6% with the fisher, '
  '20.0% at the middleman step and 44.4% at the exporter step; the same crab reaching a '
  'hotel kitchen left the fisher 27.5% and the hotel 57.0%; medium crabs bound for export '
  'were the fisher’s best case at 39.6%. Values in this range sit at the low end of what '
  'has been reported for perishable, high-value seafood. Jacinto (2004) argues that the '
  'share captured at each node tracks control of information and market access more closely '
  'than physical effort, and the ordering here matches that: the actor doing the fishing '
  'takes the smallest share and the largest accrues furthest from the water.',

  'The middleman result cuts against the usual account. Middlemen took the smallest of the '
  'three shares in every chain, between 15.5% and 20.0%, yet they are the actor fishers '
  'most often identify with the low beach price. Crona et al. (2016) reach a similar '
  'conclusion for Kenya and Zanzibar, finding middlemen blamed for outcomes settled further '
  'along the chain while operating on modest turnovers and carrying the mortality risk. '
  'Chapter Four documents that risk: 95.5% of middlemen reported daily mortality of 4 to 5 '
  'kg against 0.5 to 1 kg among fishers.',
 ],

 '5.3.5 Site Differences and What Drives Them': [
  'The actor comparison and the site comparison answer different questions, and keeping '
  'them apart was necessary: compare sites without holding the actor constant and a site '
  'with more middlemen looks like a high-price site purely because of its respondent mix. '
  'With the role held constant, fisher prices differed significantly across sites for large '
  'crabs, H(3) = 20.32, p < .001, and medium crabs, H(3) = 20.07, p < .001, while middleman '
  'prices did not, H(2) = 5.33, p = .070 and H(2) = 3.78, p = .151.',

  'That asymmetry produced the study’s sharpest contrast. At Majoreni the fisher price '
  'stood at 91.7% of the local middleman price for large crabs and 91.3% for medium, '
  'spreads of KSh 71.4 and KSh 57.1 per kilogram; at Shimoni and Vanga the same figures '
  'were 55.0% and 53.6% for large crabs, spreads of KSh 441.8 and KSh 464.3. Since fisher '
  'prices varied across sites and middleman prices did not, the narrow Majoreni gap is '
  'built on the fisher side: Majoreni traders sold at KSh 857.1, within KSh 143 of the '
  'other two sites, while Majoreni fishers were paid KSh 785.7 against roughly KSh 537 '
  'elsewhere.',

  'Two readings fit. Majoreni fishers may face a less concentrated set of first buyers, so '
  'competition at the beach lifts the first-hand price; or the seven middlemen sampled '
  'there may be first-tier buyers reselling locally rather than consolidators shipping to '
  'Mombasa, in which case their price is a shorter step from the water and the comparison '
  'is not quite like for like. This study cannot separate the two, because buyer '
  'concentration and onward destination were not measured at transaction level. Green and '
  'Clark (2021) treat dispersion at first sale as one of the more reliable indicators of '
  'weak market integration, and on that criterion Shimoni and Vanga look the weaker '
  'markets. Either way the practical implication holds: the terms a fisher gets are settled '
  'at their own landing site.',
 ],
}

out, cur, idx, dropped = [], None, 0, {}
for b in ch56:
    if b.get('k') in ('h1', 'h2', 'h3', 'h4'):
        cur = b['t']; idx = 0
        out.append(b)
        if cur in NEW:
            dropped[cur] = 0
        continue
    if cur in NEW and b.get('k') == 'p':
        dropped[cur] += 1
        if idx < len(NEW[cur]):
            out.append({'k': 'p', 't': NEW[cur][idx]}); idx += 1
        continue
    out.append(b)

bad = [k for k in NEW if dropped.get(k, 0) != len(NEW[k])]
for k in bad:
    print(f'  WARNING {k[:46]}: {dropped.get(k)} old vs {len(NEW[k])} new')
if bad:
    raise SystemExit('paragraph slots do not line up; nothing written')

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
after = sum(len(b['t'].split()) for b in out if b.get('k') in ('p', 'bul', 'num'))
json.dump(out, open(P, 'w'), ensure_ascii=False, indent=1)
for k, v in dropped.items():
    print(f'  {k[:50]:52s} {v} paragraphs kept')
print(f'\nChapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
