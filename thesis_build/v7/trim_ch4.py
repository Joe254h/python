# -*- coding: utf-8 -*-
"""Cut Chapter Four to length without losing a finding or a citation.

The three sections comparing results with previous studies ran to 1,866 words
and repeated much of Chapter Five. They are condensed to the comparisons that
are actually distinct, which keeps what the reviewer asked for in the results
chapter. Mirera (2014a), Mirera (2017a) and Fondo and Ogutu (2021) are cited
nowhere else in the thesis, so each is kept.

The three objective summaries are also shortened. They restated, sentence by
sentence, what the reader had just read.
"""
import json

P = 'v6/ch4_dedup.json'
ch4 = json.load(open(P))

NEW = {
 '4.3.5 Discussion of Findings in Relation to Previous Studies': [
  'The profile is young to middle-aged and almost entirely male, which fits accounts of '
  'the Kenyan mud crab fishery as a small-scale coastal livelihood in mangrove-dependent '
  'communities (Mirera, 2017a; Fondo & Ogutu, 2021). Fisher age was the one demographic '
  'characteristic that varied significantly by BMU, so age composition can differ from '
  'site to site even where the wider social profile does not. The near absence of women '
  'reflects a sampling frame built on landing-site registers, not an absence of women '
  'from crab-related work.',

  'Qualifications, scale, income, licensing and formality all rise together towards the '
  'downstream end of the chain. Mirera (2014a, 2017a) draws the same line between '
  'community-level harvesting and market-facing trade, though neither study establishes '
  'education as the cause of occupational position. Ownership was universal at every '
  'node, so the earnings gradient cannot be put down to who owns the enterprise. The '
  'hotelier and exporter figures rest on five and four respondents drawn mostly from '
  'outside the four BMUs, and carry that uncertainty.',

  'Credit runs vertically. Fishers borrowed from middlemen, middlemen from exporters, '
  'exporters from banks. Crona et al. (2016) describe such advances as enabling and '
  'constraining at once, solving an immediate cash problem while narrowing where the '
  'seller can sell; Béné et al. (2007) treat informal credit in small-scale fisheries as '
  'both safety net and a mechanism of persistent low returns. This survey did not record '
  'amounts, terms or duration, so it cannot say which description fits. It does show that '
  'the person lending to a fisher is the person buying from him.',

  'Learning stayed informal, with family tradition the commonest route in and formal '
  'training rare. That contrasts with the organised community-group model Mirera (2014a) '
  'examined, where organisation was central to small-scale mud crab aquaculture. Not one '
  'respondent at any node belonged to a cooperative, an association or a self-help group. '
  'Gutiérrez et al. (2011) found that leadership and visible benefits, rather than the '
  'existence of a group, separate the successful cases; that nothing survives here '
  'suggests earlier attempts offered members little they could point to. Evidence from '
  'organised aquaculture groups should not be assumed to describe independent '
  'capture-fishery actors (Fondo & Ogutu, 2021).',
 ],

 '4.4.15 Discussion of Findings in Relation to Previous Studies': [
  'Harvesting, aggregation, processing and export were each performed by a different '
  'actor category, which matches the value-chain structure described for this fishery '
  '(Mirera, 2017a; Fondo & Ogutu, 2021) and the wider account of middlemen linking '
  'dispersed harvesters to distant buyers (Crona et al., 2016). Testing each function '
  'against site rather than assuming uniformity is what this study adds: among fishers '
  'only travel time and the large- and small-crab size labels varied significantly by '
  'BMU, and among middlemen nothing did.',

  'Grading is the clearest contribution. Every actor graded, but fishers graded on weight '
  'alone while every downstream category used four criteria. Jacinto (2004) identifies '
  'this kind of informational asymmetry as a determinant of how value is shared in '
  'small-scale fisheries, and these data give a clean instance of it in a fishery where '
  'actors and functions have been documented more thoroughly than the terms of exchange '
  'between them. The site variation in labelling has not been reported before.',

  'Protection rises downstream while mortality rises with the volume held, which follows '
  'FAO (2025) on survival and quality in the live trade. The difference lies in '
  'measurement rather than direction: nobody in this chain records losses against a '
  'shared standard, so the cost of mortality cannot be attributed, priced or recovered.',

  'Prices rise at every node, as expected where later actors carry aggregation, mortality, '
  'transport and buyer-access costs. Munga and Muthumbi (2018) show for the Tana Delta '
  'that gross differentials narrow considerably once handling and transport are netted '
  'out, so none of this speaks to profit. Within that limit, the producer’s share of '
  '27.5% to 39.6% sits at the low end of what has been reported for perishable, '
  'high-value seafood, and the ordering matches Jacinto’s (2004) argument that the '
  'share captured at each node tracks control of information and market access rather '
  'than physical effort.',

  'The middleman result cuts against the popular account. Middlemen took the smallest of '
  'the three shares in every chain, yet fishers most often identify them with the low '
  'beach price. Crona et al. (2016) reach the same conclusion for Kenya and Zanzibar, '
  'finding middlemen blamed for outcomes settled further along the chain while operating '
  'on modest turnovers and carrying the mortality risk. Green and Clark (2021) treat '
  'dispersion at first sale as an indicator of weak integration; on that criterion '
  'Shimoni and Vanga are the weaker of the three markets. Because fisher prices varied '
  'significantly across sites while middleman prices did not, the mechanism sits on the '
  'fisher side of the transaction.',
 ],

 '4.5.7 Discussion of Findings in Relation to Previous Studies': [
  'Constraints differ by actor category rather than by location, which fits treatments of '
  'the value chain as a sequence of distinct risk positions rather than one system with a '
  'single binding constraint (Jacinto, 2004; Crona et al., 2016). Only the middleman '
  'constraint varied significantly by site, mortality dominating at Vanga and Majoreni '
  'and price at Shimoni. That split follows the sites where middlemen hold stock longest, '
  'which FAO (2025) identifies as a determinant of loss.',

  'Barriers to market access were near universal and no actor reported innovation or '
  'market research, consistent with national assessments of constraints in finance, '
  'organisation and formal market participation (Fondo & Ogutu, 2021). Locating those '
  'constraints by actor category rather than treating them as a general condition is the '
  'more useful form for designing an intervention.',

  'Management-plan awareness reached 95.5% of middlemen and 15.4% of fishers, the '
  'clearest institutional finding here. Njiru et al. (2021) found socioeconomic factors '
  'shaping trader participation in Beach Management Units in Kwale County, which argues '
  'for communication aimed at particular actor groups. The gap runs along the chain '
  'rather than across the map: it was not significantly associated with site.',

  'What fishers and middlemen want pulls in opposite directions, market access against '
  'price stability, and that opposition has not been reported in the Kenyan mud crab '
  'literature. It follows from the structure documented under Objective Two and means the '
  'two upstream groups cannot both be satisfied by one measure. The uniformly low rating '
  'of youth involvement also sits oddly beside the demographic evidence in this chapter, '
  'where over half the fishers were aged 18 to 35; respondents most likely read the '
  'question as formal participation rather than presence. Ndanga et al. (2013) make the '
  'same point about women in Kenyan aquaculture chains, whose participation is understated '
  'when the measure captures only formally recognised roles.',
 ],

 '4.3.4 Summary of Objective One': [
  'Objective One describes four actor categories that differ in the same direction on '
  'almost every measure. Fishers were younger, schooled to primary level or below, '
  'small-scale, minimally licensed, untrained and un-diversified, and they borrowed from '
  'the middlemen who buy from them. Middlemen were older and far more experienced. '
  'Hoteliers and exporters were formally qualified, fully licensed and operating at a '
  'scale the upstream nodes do not reach. Fisher age was the only demographic '
  'characteristic significantly associated with BMU.',
 ],

 '4.4.14 Summary of Objective Two': [
  'Objective Two shows functions dividing cleanly by node, and the information used to '
  'set value dividing with them. Fishers graded on weight alone; every other category '
  'used four criteria. Formal quality control and contact with the final buyer sat '
  'entirely downstream. Prices rose at every node and differed significantly between '
  'actor categories, first sale was concentrated at every landing site, and the harvester '
  'kept between a quarter and two fifths of the end-of-chain price.',
 ],

 '4.5.6 Summary of Objective Three': [
  'Objective Three shows constraints following the work each actor does: unstable prices '
  'and poor roads for fishers, mortality and inadequate aggregation facilities for '
  'middlemen, seasonality for hoteliers, freight cost and flight risk for exporters. '
  'Barriers to market access were close to universal, no actor had adopted new equipment '
  'or conducted market research, and management-plan awareness reached the trading node '
  'but missed the harvesting node.',
 ],
}

out, cur, replaced = [], None, {}
for b in ch4:
    if b['k'] in ('h2', 'h3'):
        cur = b['t']
        out.append(b)
        if cur in NEW:
            for t in NEW[cur]:
                out.append({'k': 'p', 't': t})
            replaced[cur] = 0
        continue
    if cur in NEW and b['k'] == 'p':
        replaced[cur] += 1          # drop the old paragraph
        continue
    out.append(b)

before = sum(len(b['t'].split()) for b in ch4 if b['k'] in ('p', 'bul', 'num'))
after = sum(len(b['t'].split()) for b in out if b['k'] in ('p', 'bul', 'num'))
json.dump(out, open(P, 'w'), ensure_ascii=False, indent=1)
for k, v in replaced.items():
    print(f'  {k[:52]:54s} {v} paragraphs -> {len(NEW[k])}')
print(f'\nChapter Four prose: {before:,} -> {after:,} words  (saved {before - after:,})')
