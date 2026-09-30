# -*- coding: utf-8 -*-
"""Deep pass over Chapters Five and Six.

Chapter Four is left untouched by instruction, so the reduction falls on the
rest. Every citation, figure and test statistic survives. The cut lands hardest
on the Implications subsections and the objective conclusions, which restate
what the preceding pages have just established.
"""
import json

P = 'v5/ch56.json'
ch56 = json.load(open(P))

REPL = {
 'This chapter interprets the findings of Chapter Four':
  'This chapter interprets the findings of Chapter Four against the literature reviewed in '
  'Chapter Two, taking the three objectives in turn. Section 5.5 brings them together under '
  'the structure-conduct-performance framework, and Section 5.6 states what the measures do '
  'and do not capture, with the limitations that bound every claim made here.',

 'Four actor categories differed systematically and in the same direction on almost every measure.':
  'Four actor categories differed systematically and in the same direction on almost every '
  'measure. Fishers were younger, schooled to primary level or below, largely unlicensed, '
  'untrained, small-scale and un-diversified; middlemen were older and far more experienced, '
  '72.7% with more than twenty years in the trade; hoteliers and exporters held certificates, '
  'diplomas or degrees, were fully licensed and operated at medium or large scale. Reported '
  'monthly income rose from KSh 8,969 among fishers to KSh 90,000 among exporters, and no '
  'respondent belonged to a cooperative, an association or a self-help group.',

 'Ninety-five of the 96 respondents were men':
  'Ninety-five of the 96 respondents were men, and the one woman was a hotelier rather than a '
  'harvester, which matches reports along the Kenyan coast that harvesting and first-tier '
  'trade are male-dominated while women appear more often in processing, retail and culture '
  'activities (Mirera, 2014a; Ochiewo et al., 2010).',

 'Why men dominate harvesting here is not something these data can settle':
  'Why men dominate harvesting here is not something these data can settle, but three '
  'mechanisms fit the setting. Harvesting is done on foot in mangrove creeks at low spring '
  'tides, often at night and away from the village, carrying mobility and safety costs that '
  'fall unequally on women (Mirera et al., 2013; Moser et al., 2005); landing-site registers '
  'and BMU membership have historically enrolled men; and the credit relationship documented '
  'in Chapter Four runs through established trading ties new entrants do not have.',

 'The consequence is methodological before it is substantive.':
  'The consequence is methodological before it is substantive. Because the fisher frame drew '
  'on landing-site registers, women working in processing, hospitality procurement, retail or '
  'crab fattening were unlikely to be reached. Ndanga et al. (2013) show that women in Kenyan '
  'aquaculture value chains concentrate in exactly the nodes such sampling misses, so the '
  'finding describes the respondents reached rather than an absence of women from the chain.',

 'Experience accumulated at the trading node rather than the harvesting node.':
  'Experience accumulated at the trading node rather than the harvesting node, which fits '
  'Mirera et al. (2013) on how local knowledge and repeated relationships shape the way crabs '
  'are found, handled and moved, and helps explain why middlemen reported regular buyers, '
  'competitive price setting and standing agreements while fishers did not. Crona et al. '
  '(2016) describe middlemen in Kenya and Zanzibar as a critical social-ecological link '
  'because that relational knowledge is not easily replaced, and Cinner et al. (2012) found '
  'age and experience shaping how artisanal fishers responded to livelihood pressure, which '
  'fits the age gap between the two nodes here. Licensing showed the same upstream weakness, '
  'and Pomeroy and Andrew (2011) argue that co-management works best where local rules are '
  'tied to a service users can see.',

 'The complete absence of collective membership matters more than a single percentage':
  'The complete absence of collective membership matters more than a single percentage '
  'suggests, since groups are the normal vehicle for price information, savings, training and '
  'dealings with government, and the literature ties organised groups and local leadership to '
  'better fishery outcomes (Gutiérrez et al., 2011; Mirera, 2014a). Without one, a fisher '
  'negotiates alone against a buyer of twenty years who knows what crabs fetch further up.',

 'Forming groups is not itself the remedy.':
  'Forming groups is not itself the remedy: Gutiérrez et al. (2011) found leadership and '
  'clear incentives, not the existence of a group, separate the successful cases. That '
  'nothing exists here at any node suggests earlier attempts offered members nothing they '
  'could see.',

 'No fisher used a formal loan, yet 93.8% named a middleman as their main source':
  'No fisher used a formal loan, yet 93.8% named a middleman as their main source of credit '
  'and close to two in five were paid at least partly on credit by the buyer purchasing from '
  'them. Crona et al. (2016) describe such arrangements as enabling and constraining at once, '
  'the advance solving this week’s cash problem while narrowing where the fisher can sell, '
  'and Béné et al. (2007) treat informal credit in small-scale fisheries as both safety net '
  'and mechanism of persistent low returns.',

 'Which of the two dominates here cannot be judged from this study':
  'Which dominates here cannot be judged, since amounts, terms and duration went unrecorded. '
  'What can be said is that the person extending the credit is the person setting the price '
  'the fisher calls fixed, and that no alternative source of working capital was reported at '
  'the harvesting node.',

 'Theoretically, the profile results support treating actor category':
  'The profile results support treating actor category rather than location as the primary '
  'structural variable in this market: differences between the four categories were large '
  'and consistent, those between landing sites fewer and mostly confined to fishers. In '
  'practice they identify three entry points needing no new infrastructure, a licensing route '
  'upstream actors can complete, a source of working capital that is not the buyer, and a '
  'collective body with a service attached.',
 'Practically, the results identify three entry points': None,

 'Functions divided cleanly by node and so did the information attached to them.':
  'Functions divided cleanly by node and so did the information attached to them. Fishers '
  'harvested, tied claws, packed in sacks and walked to the landing site; middlemen '
  'aggregated, cleaned, sorted, graded on a four-criterion rule and moved crabs by vehicle or '
  'boat; hoteliers processed and froze; exporters packed Styrofoam under inspection and '
  'certification. Prices rose at every node and differed significantly between actor '
  'categories, and among fishers by site as well. Multi-stage chains of this kind have been '
  'described for Bangladesh, the Philippines and coastal Tanzania (ACDI/VOCA, 2005; Mahmud & '
  'Mamun, 2013; Sultana et al., 2018).',

 'Every actor said they graded.':
  'Every actor said they graded, but not by the same rule: all 65 fishers used weight alone '
  'while 95.5% of middlemen and every hotelier and exporter combined size, weight, shell '
  'condition and claw size. Jacinto (2004) identifies this kind of informational asymmetry as '
  'a determinant of how value is distributed in small-scale fisheries, and these data supply '
  'a clean instance of it.',

 'The site variation in grading language reinforces the point.':
  'The site variation in grading language reinforces the point. At Shimoni 44.0% of fishers '
  'described their large category as mixed and 36.0% did the same for the small category, '
  'while fishers elsewhere used the plain labels, χ²(3, N = 63) = 16.87, p = .001 and χ²(3, N '
  '= 63) = 15.96, p = .002. The survey recorded the label, not a measured carapace width, so '
  'this is vocabulary rather than biology, but it carries a cost: a Shimoni fisher and his '
  'buyer may not mean the same thing by large, and that is when a grading dispute goes the '
  'better-informed party’s way.',

 'Packaging became more protective downstream':
  'Packaging became more protective downstream, from sacks to crates to Styrofoam, and '
  'reported mortality rose with the volume each actor held; survival and quality in the live '
  'trade turn on handling, containment and transport (FAO, 2025). The absence of formal '
  'quality control upstream does not mean no care was taken, since fishers tied claws and '
  'middlemen cleaned and sorted. The weakness is that neither procedures nor losses were '
  'documented against a shared standard, so the cost of mortality cannot be priced into a '
  'grade or recovered through it.',

 'Reported prices rose at every node and the actor comparisons were unambiguous':
  'Reported prices rose at every node and the actor comparisons were unambiguous, H(3) = '
  '55.84, p < .001 for large crabs and H(3) = 38.00, p < .001 for medium. Rising prices are '
  'expected where later actors carry aggregation, mortality, transport and buyer-access '
  'costs, but these are gross prices: Munga and Muthumbi (2018) show for the Tana Delta that '
  'gross differentials narrow considerably once handling and transport are netted out. '
  'Expressed as marketing margins, the chain took 60.4% to 72.5% of the final price before it '
  'reached the harvester, within a structure Table 40 describes as an HHI of 2,371 and 76.9% '
  'of harvesters dealing with a single buyer.',

 'Within that limit, each node’s price as a share of the end-of-chain price':
  'A large crab reaching an exporter left 35.6% with the fisher, 20.0% at the middleman step '
  'and 44.4% at the exporter step; the same crab reaching a hotel kitchen left the fisher '
  '27.5% and the hotel 57.0%; medium crabs bound for export were the fisher’s best case at '
  '39.6%. Values in this range sit at the low end of what has been reported for perishable, '
  'high-value seafood, and Jacinto (2004) argues that the share captured at each node tracks '
  'control of information and market access more closely than physical effort, which is the '
  'ordering here.',

 'The middleman result cuts against the usual account.':
  'The middleman result cuts against the usual account: middlemen took the smallest of the '
  'three shares in every chain, between 15.5% and 20.0%, yet fishers most often identify them '
  'with the low beach price. Crona et al. (2016) reach a similar conclusion for Kenya and '
  'Zanzibar, finding middlemen blamed for outcomes settled further along the chain while '
  'carrying the mortality risk, which Chapter Four documents at 4 to 5 kg a day against 0.5 '
  'to 1 kg among fishers.',

 'The actor comparison and the site comparison answer different questions':
  'The actor and site comparisons answer different questions, and keeping them apart '
  'mattered: compare sites without holding the actor constant and a site with more middlemen '
  'looks like a high-price site purely through its respondent mix. With the role held '
  'constant, fisher prices differed significantly across sites for large crabs, H(3) = 20.32, '
  'p < .001, and medium, H(3) = 20.07, p < .001, while middleman prices did not, H(2) = 5.33, '
  'p = .070 and H(2) = 3.78, p = .151.',

 'That asymmetry produced the study’s sharpest contrast.':
  'That asymmetry produced the study’s sharpest contrast. At Majoreni the fisher price stood '
  'at 91.7% of the local middleman price for large crabs and 91.3% for medium, spreads of KSh '
  '71.4 and KSh 57.1 per kilogram; at Shimoni and Vanga the same figures were 55.0% and '
  '53.6%, spreads of KSh 441.8 and KSh 464.3. The narrow Majoreni gap is built on the fisher '
  'side: its traders sold at KSh 857.1, within KSh 143 of the other two sites, while its '
  'fishers were paid KSh 785.7 against roughly KSh 537 elsewhere.',

 'Two readings fit.':
  'Two readings fit. Majoreni fishers may face a less concentrated set of first buyers, so '
  'competition at the beach lifts the price; or the seven middlemen sampled there may be '
  'first-tier buyers reselling locally rather than consolidators shipping to Mombasa, making '
  'the comparison not quite like for like. This study cannot separate them, since buyer '
  'concentration and onward destination were not measured at transaction level. Green and '
  'Clark (2021) treat dispersion at first sale as a reliable indicator of weak integration, '
  'and on that criterion Shimoni and Vanga look the weaker markets.',

 'The hotelier medium-grade mean of KSh 380.0 per kilogram does not fit':
  'The hotelier medium-grade mean of KSh 380.0 per kilogram does not fit the pattern, sitting '
  'below the fisher price for the same grade and far below the same respondents’ large-crab '
  'mean of KSh 2,200.0. The entries may refer to a different product form, unit or '
  'transaction, in which case the value is correct but not comparable, or they may be a '
  'field-entry error. They were retained for fidelity to the source data and excluded from '
  'the chain calculation, but should be confirmed against the questionnaires before any '
  'argument about value addition uses them.',

 'Theoretically, these results locate the mechanism of value capture':
  'These results locate the mechanism of value capture in control of the grading rule and of '
  'the connection to the final buyer, rather than in harvesting effort or the middleman’s '
  'margin, which is this study’s contribution to a literature that has documented actors and '
  'functions more thoroughly than the distribution of returns among them. Two interventions '
  'follow and neither needs capital: a written grading standard both parties to a first sale '
  'can read, and an independent record of what grades are fetching.',
 'Practically, two interventions follow directly from the numbers': None,

 'No constraint was shared across the chain.':
  'No constraint was shared across the chain: fishers named price fluctuation and poor roads, '
  'middlemen mortality and the lack of aggregation facilities, hoteliers seasonality, '
  'exporters freight and flight delays. Barriers to market access were reported by 95.8% of '
  'respondents, no actor had adopted new equipment or conducted market research, and '
  'management-plan awareness reached 95.5% of middlemen and every exporter but only 15.4% of '
  'fishers and no hotelier.',

 'Each constraint follows from the work the actor does.':
  'Each constraint follows from the work the actor does. The fisher sells the same day at a '
  'price he does not set, so volatility reaches him first; the middleman holds stock, so he '
  'loses crabs, mortality being named by half of them and by all four Vanga middlemen; the '
  'hotelier feels the season and the exporter the freight. One chain-wide intervention will '
  'not reach all four, which is why the recommendations in Chapter Six are written by actor '
  'category.',

 'The infrastructure answers point the same way.':
  'The infrastructure answers point the same way. Poor roads dominated fisher responses at '
  '98.5% while 90.9% of middlemen named the lack of aggregation facilities. Access routes '
  'would improve movement from landing areas but not reduce holding losses; aggregation '
  'facilities would improve shade, loading and live-crab management but would not widen '
  'fisher buyer choice unless linked to transport and price information.',

 'Negative views of market organisation sit comfortably':
  'Negative views of market organisation sit comfortably with everything else recorded here: '
  'no collective membership, low upstream licensing, informal grading, no market research and '
  'fixed prices reported by every fisher. Awareness of the management plan followed '
  'commercial position rather than geography, so information moves along commercial '
  'relationships instead of the co-management structures built to carry it.',

 'Beach Management Units remain the most practical institutions':
  'Beach Management Units remain the most practical institutions for narrowing that gap. '
  'Njiru et al. (2021) found socioeconomic factors influencing trader participation in BMUs '
  'in Kwale County, which supports communication designed for specific actor groups. The '
  'large neutral response among fishers on the policy framework is not approval; set beside '
  '15.4% awareness it more likely reflects unfamiliarity.',

 'Fishers chose market-access improvement, 86.2% of them':
  'Fishers chose market-access improvement, 86.2% of them, while middlemen chose price '
  'stability, 95.5%. These are two views of one exchange: the fisher wants an alternative to '
  'the buyer in front of him, the middleman wants the price to hold still while he carries '
  'stock and credit risk. Better market access for fishers means more competition for '
  'middlemen, so splitting the difference will not reconcile them, whereas better price '
  'information and clearer grades reduce uncertainty for both.',

 'Reported youth involvement was low or very low throughout':
  'Reported youth involvement was low or very low throughout, even though more than half the '
  'fishers were aged 18 to 35 and four were under 18. Respondents may have read the question '
  'as formal participation or ownership rather than presence, so future questionnaires should '
  'define it directly; the presence of minors in harvesting also raises safeguarding and '
  'schooling questions this study was not designed to answer.',

 'Theoretically, the constraint results show that performance in this chain':
  'The constraint results show performance in this chain bounded at different points for '
  'different actors, an argument against treating the value chain as one system with a single '
  'binding constraint. In practice an intervention budget spent uniformly across nodes will '
  'be largely wasted, and the sequence matters as much as the content.',

 'Set against the structure-conduct-performance framework':
  'Set against the structure-conduct-performance framework, the three objectives describe a '
  'single system. The structure is concentrated at first sale: an HHI of 2,371 across the '
  'four BMUs and 8,580 at the tightest, 76.9% of harvesters selling to a single buyer and '
  '2.95 harvesters for every trader sampled, with entry downstream needing licences, capital '
  'and buyer contacts upstream actors lack and no collective body at any node.',

 'Conduct follows from that structure.':
  'Conduct follows. Buyers set prices and every fisher accepted them as fixed, grading runs '
  'on a rule only the buyer fully controls, credit advances tie sellers to particular buyers, '
  'and nobody conducts market research, so information travels through the same relationships '
  'that set the prices.',

 'Performance is what that structure and conduct would predict.':
  'Performance is what that would predict. Income ran from KSh 8,969 among fishers to KSh '
  '90,000 among exporters, the fisher’s share of the end-of-chain price between 27.5% and '
  '39.6%, the total marketing margin from 60.4% to 72.5%, and dispersion fell from a '
  'coefficient of variation of 31.8% to 6.8% for the large grade, which Green and Clark '
  '(2021) treat as a signature of weak integration at first sale.',

 'This has a practical edge.':
  'Measures aimed only at production are therefore unlikely to shift how value is '
  'distributed, because the binding constraint is not how many crabs come ashore but the '
  'terms on which they change hands: the grading rule, whether a fisher has independent price '
  'information, and the credit relationship.',

 'Three dimensions of market structure that the literature treats as standard':
  'Three dimensions of market structure that the literature treats as standard cannot be '
  'computed here as a transaction survey would compute them. Each has a counterpart these '
  'data support, reported in Chapter Four.',

 'Concentration is measured over harvesters rather than volume.':
  'Concentration is measured over harvesters rather than volume, because a textbook ratio '
  'needs a census of buyers and the quantity each handles and the survey recorded where every '
  'fisher took his catch instead. Table 40 therefore weights buying points by the share of '
  'harvesters attached to each: an HHI of 2,371 across the four BMUs and 8,580 at Majoreni, '
  'where a numbers-equivalent of 1.17 outlets means one buying point in practice, putting '
  'every BMU above the 2,500 mark conventionally treated as high concentration. What it '
  'cannot say is how much crab passes through each point.',

 'Margins are measured gross, and net of one cost.':
  'Margins are measured gross, and net of one cost. Table 43 gives the gross marketing margin '
  'at each node, a total of 60.4% to 72.5% of the final price and a producer’s share of 27.5% '
  'to 39.6%. No transport, holding, ice, packaging or capital cost was priced, so none of '
  'these is a profit; physical mortality was measured, and carrying it through cuts the '
  'producer’s share by roughly a tenth, to between 24.6% and 35.5%.',

 'Efficiency is approached through dispersion rather than cost':
  'Efficiency is approached through dispersion rather than cost, the cost side being missing. '
  'Table 44 gives two indicators that do not need it: price dispersion falls from a '
  'coefficient of variation of 31.8% among fishers to 14.9% among middlemen and 6.8% among '
  'exporters for the large grade, so price uncertainty sits almost entirely at the harvesting '
  'node; and price transmission ran from 53.6% at Vanga to 91.7% at Majoreni.',

 'The sample was not fully probabilistic.':
  'The sample was not fully probabilistic. Reliable lists were unavailable downstream, so '
  'referral and convenience procedures were used and the findings describe the respondents '
  'reached rather than population estimates. The achieved fisher sample of 65 fell short of '
  'the calculated 83, a coverage rate of 78.3%, snowball sampling may over-represent actors '
  'with stronger trading connections, and only five hoteliers and four exporters were '
  'sampled, with no middleman at Msambweni and only three fishers there.',

 'The design was cross-sectional and covered a single survey period,':
  'The design was cross-sectional over a single survey period, so seasonal variation is not '
  'captured and no causal direction can be established, and prices, income and losses were '
  'self-reported. Sixty-eight categorical tests were run without a correction for multiple '
  'comparisons, so associations close to .05 are exploratory. What remains genuinely '
  'unmeasured is the volume behind each transaction and the costs each actor carries, both '
  'following from an instrument designed as an actor inventory rather than a transaction '
  'survey. Section 6.5 sets out the data collection that would close them.',

 # ---------------------------------------------------------------- Chapter Six
 'This chapter draws conclusions from the three objectives':
  'This chapter draws conclusions from the three objectives and sets out recommendations, '
  'each resting on evidence reported in Chapter Four and naming the body best placed to act.',

 'The four actor categories differ systematically and in the same direction':
  'The four actor categories differ systematically and in the same direction on almost every '
  'characteristic measured. Fishers are younger, schooled to primary level or below, '
  'small-scale, minimally licensed, untrained and un-diversified, and borrow from the '
  'middlemen who buy from them; middlemen are older, more experienced and better capitalised; '
  'hoteliers and exporters are formally qualified, fully licensed and operating at a scale '
  'upstream actors do not reach. No respondent belonged to a cooperative or a self-help '
  'group.',

 'The chain runs as a functional sequence':
  'The chain runs as a functional sequence from harvesting through aggregation to processing '
  'and export, with the information used to assign value concentrated downstream: fishers '
  'graded on weight alone while every other category used four criteria, and formal quality '
  'control and contact with the final buyer sat entirely downstream. The fisher retained '
  '27.5% to 39.6% of the price the crab eventually fetched, the middleman added 15.5% to '
  '20.0%, and 44.4% to 57.0% was added at the final buyer. The first-sale gap was set '
  'locally: Majoreni fishers held 91.7% of the middleman price for large crabs where Shimoni '
  'and Vanga fishers held close to 54%. Price here follows position in the chain, control of '
  'the grading rule and access to alternative buyers, not harvesting effort.',

 'Constraints arise at different points':
  'Constraints arise at different points and follow the work each actor does: unstable prices '
  'and poor roads for fishers, mortality and inadequate aggregation facilities for middlemen, '
  'seasonality for hoteliers, freight and flight risk for exporters. Barriers to market '
  'access were close to universal, no actor had adopted new equipment or conducted market '
  'research, and management-plan awareness reached traders and exporters while missing '
  'fishers and hoteliers. Improvement therefore requires coordinated but actor-specific '
  'measures.',

 'The South Coast mud crab market is commercially active and institutionally uneven.':
  'The South Coast mud crab market is commercially active and institutionally uneven. Fishers '
  'supply the product with almost no institutional support, while middlemen and downstream '
  'actors hold the grading, the logistics and the connection to high-value buyers. Site '
  'matters for the age of the fishing population, the words used for grades, the price '
  'fishers receive and the constraint middlemen name, but the steadier divide runs between '
  'market nodes. Improvement should start where the terms of exchange are set: a shared '
  'grading standard, a reliable public price record, better live-crab handling, '
  'infrastructure at both ends of the chain, licensing people can obtain, and communication '
  'that reaches harvesters as dependably as traders.',

 'Each recommendation below states the problem': None,
}

before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p', 'bul', 'num'))
hit, dropped = set(), 0
out = []
for b in ch56:
    if b.get('k') not in ('p', 'bul', 'num'):
        out.append(b); continue
    matched = None
    for opener, new in REPL.items():
        if opener in hit or not b['t'].startswith(opener):
            continue
        matched = (opener, new); break
    if matched is None:
        out.append(b); continue
    opener, new = matched
    hit.add(opener)
    if new is None:
        dropped += 1
    else:
        b['t'] = new; out.append(b)

missing = [o[:58] for o in REPL if o not in hit]
if missing:
    print('NOT FOUND, nothing saved:')
    for m in missing: print('   ', m)
    raise SystemExit(1)
after = sum(len(b['t'].split()) for b in out if b.get('k') in ('p', 'bul', 'num'))
json.dump(out, open(P, 'w'), ensure_ascii=False, indent=1)
print(f'paragraphs rewritten: {len(hit) - dropped}   removed: {dropped}')
print(f'Chapters Five and Six prose: {before:,} -> {after:,} (saved {before - after:,})')
