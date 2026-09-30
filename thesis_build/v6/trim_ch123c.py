# -*- coding: utf-8 -*-
"""Third pass over Chapter Two, and a second over Chapter Three.

Chapter Four is fixed by instruction, so the literature review and the methods
carry the rest of the reduction. Every citation is kept and every section keeps
its claim; paired paragraphs are merged into one.
"""
import docx
from docx.oxml.ns import qn

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)


def retext(p, t):
    runs = p._p.findall(qn('w:r'))
    if not runs:
        return False
    keep = runs[0]
    for r in runs[1:]:
        p._p.remove(r)
    for old in keep.findall(qn('w:t')):
        keep.remove(old)
    tn = keep.makeelement(qn('w:t'), {})
    tn.set(qn('xml:space'), 'preserve')
    tn.text = t
    keep.append(tn)
    return True


EDITS = {
 'The genus Scylla contains four recognised mud crab species':
  'The genus Scylla contains four recognised mud crab species: S. serrata, S. tranquebarica, '
  'S. olivacea and S. paramamosain (Ogawa et al., 2011), found in mangrove estuaries and '
  'coastal waters of the Indian and Pacific oceans. Scylla serrata grows by moulting, adults '
  'exceeding 2 kg and 250 mm carapace width (Webley, 2008); females migrate offshore to '
  'spawn, and the species is a benthic predator and cannibalistic (Allan & Fielder, 2003).',

 'Fishing grounds and capture methods vary with the target crab':
  'Fishing grounds and capture methods vary with the target crab, habitat, tide, gear and the '
  'fisher’s experience (Mirera, 2017a), and include hand collection, hooks and sticks, baited '
  'pots or traps, scoop or seine nets and hooked metal rods (Richmond et al., 2006; Bonine et '
  'al., 2008). Kenyan fishers commonly work on foot, taking crabs from mangrove burrows '
  'around low spring tides and relying on knowledge of burrows and tidal creeks rather than '
  'specialised equipment (Moser et al., 2005; Fondo et al., 2020; Mirera et al., 2013). '
  'Catches may be held at home for several days until enough accumulate for sale (Ochiewo et '
  'al., 2010), which makes survival part of the marketing problem. Mud crab fishers do not '
  'always use the formal landing sites or licences the Fisheries Management and Development '
  'Act, 2016 provides for, so catches may stay outside routine landing records.',
 'Many work on foot and rely on knowledge of burrows and tidal creeks': None,

 'Scylla serrata is among the more valuable shellfish harvested':
  'Scylla serrata is among the more valuable shellfish harvested from tropical mangroves, and '
  'its commercial growth on the South Coast has created a longer market chain rather than '
  'replacing small-scale production (FAO, 2025). Demand for live crabs raises both harvesting '
  'pressure and the value of keeping crabs alive, and regional evidence suggests that buyer '
  'concentration, grade setting and market access shape prices and the distribution of gross '
  'returns (Jacinto, 2004; Crona et al., 2016).',

 'The fishery involves fishers, brokers or middlemen, traders':
  'The fishery involves fishers, brokers or middlemen, traders, wholesalers, retailers and '
  'final buyers: fishers are small-scale operators using hand collection or simple gear '
  '(Mirera et al., 2013), the others aggregate, grade, transport, process or sell the catch. '
  'Participation differs by age, experience, education, gender and access to finance, with '
  'harvesting and formal leadership largely male-dominated and women more visible in trade, '
  'processing and crab fattening (Ochiewo et al., 2010; Mirera, 2014a). Earlier studies place '
  'many Kenyan crab fishers between 23 and 55 years of age and report primary education as '
  'far more common than secondary (Fulanda et al., 2009; Ndanga et al., 2013), though that '
  'context cannot show whether profiles are the same across BMUs.',
 'Participation differs by age, experience, education, gender and access': None,

 'Functions change as crabs move through the chain.':
  'Functions change along the chain. Fishers capture crabs by hand, from burrows or with '
  'baited gear, and the method affects size, condition and survival, which bear on the first '
  'sale price (Sultana et al., 2018). Middlemen buy at landing sites, combine catches, grade '
  'and arrange holding and transport, which connects fishers to distant buyers but may also '
  'give them an information advantage. Wholesalers, retailers, hotels and exporters emphasise '
  'consistent quality and survival (FAO, 2025), so the chain is better read as a sequence of '
  'functions than as one group of traders.',
 'Wholesalers, retailers, hotels, restaurants and exporters emphasise': None,

 'Mud crab trade depends on keeping a live, perishable product':
  'Mud crab trade depends on keeping a live, perishable product saleable, so grading, price '
  'setting, transport, packaging and payment are part of production economics (FAO, 2025). '
  'Whoever controls grading or transport may reach a higher-value buyer, and whoever holds '
  'live crabs bears the mortality and the rejected consignment.',

 'Crabs are commonly graded by size, weight, sex, shell hardness':
  'Crabs are graded by size, weight, sex, shell hardness and condition, large hard-shell '
  'crabs being preferred for meat content and transport tolerance, males sometimes fetching '
  'more and berried females sometimes restricted (FAO, 2025). Grading may happen at the '
  'landing site or after aggregation, and where the criteria are informal or applied visually '
  'a fisher may be unable to verify why a crab was placed in a particular grade. The issue is '
  'not grading itself but whether the criteria and their price consequences are transparent.',
 'Grading may happen at the landing site or after a middleman': None,

 'Mud crab prices vary with grade, season, demand, distance to market':
  'Prices vary with grade, season, demand, distance to market and whether crabs are sold '
  'alive, large live crabs generally fetching more in urban, hotel and export markets (FAO, '
  '2025). Small-scale fishers may accept a buyer’s price when they lack holding facilities, '
  'need cash or depend on that buyer for transport and credit; informal agreements cut '
  'transaction costs but can make the basis of a price hard to challenge (Crona et al., '
  '2016).',
 'Small-scale fishers may accept a buyer’s price when they lack holding': None,

 'Transport affects survival and quality.':
  'Transport affects survival and quality. Live crabs are vulnerable to heat, dehydration and '
  'handling stress, so traders use baskets, plastic crates or wooden boxes, often with damp '
  'material. Long distances, poor roads and limited cold-chain or live-holding facilities add '
  'to the risk in the region; shorter journeys and better containment may cut mortality '
  'without more fishing effort, and the question is which actors have those options.',
 'Long distances, poor roads and limited cold-chain or live-holding': None,

 'Packaging controls movement, moisture and physical damage':
  'Packaging controls movement, moisture and damage in transit: live crabs may be tied or '
  'separated to reduce injury and cannibalism, and containers must ventilate and protect '
  'claws and legs. Export markets require consistent packaging, labels and traceability while '
  'small-scale traders use low-cost local materials, and the trade-off between container '
  'cost, survival and reusability should be assessed rather than assumed.',
 'Export markets often require consistent packaging, labels and traceability,': None,

 'Cash remains common at landing sites because fishers need immediate income,':
  'Cash remains common at landing sites because fishers need immediate income, though payment '
  'may be delayed until a broker has sold the crabs (Crona et al., 2016). Buyers may also '
  'advance cash or gear for continued or exclusive supply, which Crona et al. (2016) describe '
  'as solving a short-term financing problem while narrowing the seller’s choice of buyer. '
  'Whether mobile money changes that balance is taken up in Chapter Four.',
 'Buyers may also advance cash or gear in return for continued or exclusive supply,': None,

 'Mud crab actors face ecological, operational and market constraints.':
  'Actors face ecological, operational and market constraints. Fishers report seasonal '
  'availability and declining catches where juvenile or berried crabs are taken and mangroves '
  'degraded, while traders must keep live crabs saleable while assembling volume. Limited '
  'credit, unstable prices, poor holding facilities and dependence on a few brokers reduce '
  'bargaining options, and weak enforcement of size rules may let short-term demand undermine '
  'the resource (Mirera, 2017a).',
 'Limited credit, unstable prices, inadequate holding facilities': None,

 'Demand for large, healthy crabs leaves room for better handling':
  'Demand for large, healthy crabs leaves room for better handling, clearer grades and '
  'higher-value products, and crab fattening can raise sale weight, though its value depends '
  'on survival, feed, labour, seed and a confirmed buyer (Mirera, 2014b). Community '
  'participation in size limits and temporary closures has improved awareness and quality in '
  'co-managed fisheries (Gutiérrez et al., 2011); the lesson is that market incentives and '
  'local enforcement need designing together.',
 'Community participation in size limits and temporary closures': None,

 'The Fisheries Management and Development Act, No. 35 of 2016 (Cap. 378) is the main':
  'The Fisheries Management and Development Act, No. 35 of 2016 (Cap. 378) is the main '
  'national framework for conservation, management and development of fisheries resources '
  'and recognises co-management through Beach Management Units, with governance shared '
  'between national and county institutions. The Fisheries Management and Development (Safety '
  'and Quality) Regulations, 2024 govern handling, movement and marketing, their licensing, '
  'traceability, hygiene and quality requirements bearing on traders and exporters seeking '
  'formal markets. Kenya’s Blue Economy commitments add emphasis on traceability, monitoring '
  'and value-chain development (Fondo & Ogutu, 2021), where the practical gaps remain '
  'awareness, compliance support and enforcement.',
 'The Fisheries Management and Development (Safety and Quality) Regulations, 2024 address': None,

 'Three findings recur across settings and methods':
  'Three findings recur and can be treated as reasonably secure. Mud crab chains in the '
  'region are a sequence of distinct functions rather than one trading group (Mirera, 2017a; '
  'Jacinto, 2004; FAO, 2025); survival of a live product governs value, so handling and '
  'holding time are production economics (Mirera et al., 2013); and small-scale harvesters '
  'work with limited finance, organisation and market access (Béné et al., 2007; Fondo & '
  'Ogutu, 2021). This study tests all three against one dataset.',

 'The clearest disagreement is whether middlemen improve or reduce':
  'The clearest disagreement is whether middlemen improve or reduce the position of fishers. '
  'Jacinto (2004) argues that the share of final value captured at each node follows control '
  'of information and market access rather than physical effort, so an actor between '
  'harvester and buyer captures value the harvester cannot reach, and Béné et al. (2007) '
  'treat an advance against future supply as a mechanism of persistent low returns. Crona et '
  'al. (2016) reach almost the opposite conclusion, describing middlemen as a critical '
  'social-ecological link whose relational knowledge is not easily replaced, blamed for '
  'outcomes settled further along the chain while carrying the mortality risk.',
 'A second line reaches almost the opposite conclusion.': None,

 'The two make different empirical claims':
  'The two make different empirical claims, one about who captures the value and one about '
  'what the middleman’s position returns once risk is counted, so resolving them needs the '
  'price at each node and the share each holds in the same chain. No study reports that for a '
  'Kenyan mud crab chain, which is the first gap this study addresses.',

 'A second disagreement concerns grading.':
  'A second disagreement concerns grading. FAO (2025) treats grading by size, weight, shell '
  'condition and claw size as a legitimate quality signal; Jacinto (2004) treats it as '
  'informational asymmetry, since a criterion the buyer applies and the seller cannot verify '
  'transfers value rather than signalling it. Both may hold, but only if the rule is applied '
  'consistently and both parties can read it.',

 'Four limitations recur in the work reviewed above.':
  'Four limitations recur. The first is a production focus: much of the Kenyan mud crab '
  'literature is biological, ecological or aquacultural (Mirera, 2017a, 2017b; Mirera & '
  'Mosknes, 2015; Moser et al., 2005; Webley, 2008), not designed to describe exchange. The '
  'second is a setting mismatch: organisation and training have been studied in community '
  'aquaculture groups rather than independent capture-fishery actors (Mirera, 2014a).',
 'The second is a setting mismatch:': None,

 'The third is aggregation:':
  'The third is aggregation: regional and national assessments report at sector level (Fondo '
  '& Ogutu, 2021; Béné et al., 2007), so they cannot say which actor category faces which '
  'constraint. The fourth is the absence of cost data, which this study shares; Munga and '
  'Muthumbi (2018) show for the Tana Delta that gross price differentials narrow considerably '
  'once handling and transport are netted out, so any study reporting gross prices must stop '
  'short of claims about profit.',
 'The fourth is the absence of cost data': None,

 'The literature specific to this coast is thinner and weighted towards production.':
  'The literature specific to this coast is thinner and weighted towards production. Mirera '
  'et al. (2013) document fishing tactics and traditional knowledge; Ochiewo et al. (2010) '
  'and Mirera (2014a) record the gendered division of the fishery; Fondo et al. (2020) '
  'describe the national status of the fishery and Fondo and Ogutu (2021) place it within the '
  'Blue Economy agenda; and Fulanda et al. (2009) and Kimani et al. (2018) supply the fisher '
  'population figures behind this study’s sampling frame. Kwale County appears mainly as a '
  'location: Njiru et al. (2021) treat its institutions directly, finding trader '
  'participation in Beach Management Units varies with the trader’s own circumstances.',
 'Kwale County appears mainly as a location rather than a subject.': None,

 'So prices at each node in a Kwale mud crab chain have not been reported':
  'So prices at each node in a Kwale mud crab chain have not been reported, the grading '
  'criteria each actor category uses have not been recorded, and no study has tested whether '
  'actor characteristics, functions or constraints differ between the BMUs of this coast.',

 'The gap is specific.':
  'The gap is specific. Previous work establishes that mud crab chains are functionally '
  'differentiated, that survival governs value and that small-scale harvesters are '
  'institutionally weak, but not how the value of a South Coast mud crab is divided between '
  'those who catch, trade and sell it, whether the grading rule behind that division is '
  'shared or asymmetric, or whether any of it varies between Beach Management Units. Those '
  'three questions are the three objectives of this study.',

 'This study uses the Structure-Conduct-Performance (SCP) paradigm':
  'This study uses the Structure-Conduct-Performance paradigm as its main analytical '
  'framework, commonly applied in agricultural and fisheries marketing to organise evidence '
  'on market structure, actor conduct and market outcomes. It guides interpretation and is '
  'not used to claim a causal sequence. Structure is described through the number and types '
  'of actors, their characteristics, entry conditions, licensing, capital, collective '
  'organisation and buyer connections; conduct covers sourcing, grading, handling, pricing, '
  'payment, transport and credit; performance through the descriptive indicators the dataset '
  'holds.',
 'Market structure is described through the number and types of actors,': None,

 'Value-chain concepts map crabs from harvesting':
  'Value-chain concepts map crabs from harvesting through aggregation, hospitality and '
  'export, not as a second causal theory, and the sustainable livelihoods framework of '
  'Allison and Ellis (2001) gives background for reading education, experience, finance and '
  'collective membership.',

 'Figure 3 organises the study variables by objective':
  'Figure 3 organises the study variables by objective. It is descriptive, not a causal '
  'model: the arrows show the order in which structure, conduct and outcomes were examined, '
  'not estimated effects.',

 'Objective One describes market structure and actor profiles using actor category,':
  'Objective One uses actor category, BMU, age, gender, education, experience, scale, '
  'licensing, collective membership and credit, summarised by actor category and compared '
  'across BMUs where coverage allowed. Objective Two examines conduct at each node: sourcing, '
  'grading, handling, packaging, transport, pricing, payment, buyer relations and market '
  'research, with income, prices, market access and losses as descriptive outcomes rather '
  'than a performance index. Objective Three describes the infrastructure, market barriers, '
  'policy awareness, risks and opportunities each category reported. No mediation or '
  'moderation model was estimated.',

 # =============================================== Chapter Three, second pass
 'This chapter describes the study design, site, target population':
  'This chapter describes the design, site, target population, sampling, data collection and '
  'analysis used to describe the actors, functions, constraints and opportunities in the '
  'Kwale County mud crab market.',

 'The study was conducted on the South Coast of Kenya, mainly in Kwale County':
  'The study was conducted on the South Coast of Kenya, mainly in Kwale County, between '
  'latitudes 3.05 and 4.75 degrees South and longitudes 38.52 and 39.51 degrees East (Figure '
  '4). The county covers about 8,270.2 square kilometres from Likoni to Vanga, where mangrove '
  'forests, tidal creeks and shallow waters provide habitat for Scylla serrata (Mirera, '
  '2017a; Fondo et al., 2020), and was selected as an established harvesting and trading '
  'area. Its 20 Beach Management Units and 54 landing sites regulate fishing and manage the '
  'sites where fishers sell to brokers and traders (Njiru et al., 2021), which makes them the '
  'right places to collect data on grading, pricing, transport, packaging and payment. '
  'Tourism and urban markets generate high demand for live crabs (FAO, 2025), so the fishery '
  'has shifted from subsistence towards a market-oriented activity.',
 'The county has 20 Beach Management Units and 54 landing sites,': None,

 'The study used a cross-sectional descriptive mixed-methods design.':
  'The study used a cross-sectional descriptive mixed-methods design. Each respondent was '
  'surveyed once, with field observations and key-informant interviews supplying context. It '
  'supports actor profiles, comparisons among actor categories and exploratory BMU '
  'associations, but establishes no causal pathway and no seasonal change.',

 'The target population comprised mud crab fishers':
  # fix_refs.py prepends the Lamm and Lamm (2019) definition by swapping this
  # first sentence, so it has to stay word for word
  'The target population comprised mud crab fishers, middlemen, hoteliers and exporters '
  'operating in Kwale County. These groups harvest, handle, aggregate, process or '
  'trade mud crabs and so correspond to the three objectives. Consumers, restaurants that did '
  'not procure directly, input suppliers and other service providers were outside the survey '
  'scope. Ministry of Fisheries records informed the fisher sampling frame; complete lists '
  'did not exist for the other three groups, whose accessible population depended on '
  'referrals and availability.',

 'The completed survey covered 96 actors: 65 fishers':
  'The completed survey covered 96 actors: 65 fishers, 22 middlemen, five hoteliers and four '
  'exporters. Fishers were recruited from the selected BMUs; because no complete lists of '
  'downstream actors existed, respondents identified traders and buyers who could be '
  'approached, and those referrals were followed through snowball sampling.',

 'The study reached 65 of the target 83 fishers, 78.3%':
  'The study reached 65 of the target 83 fishers, 78.3%, mainly because some moved among '
  'landing sites and were absent during scheduled visits, so site-level percentages for BMUs '
  'with few respondents should be read cautiously. No conventional response rate could be '
  'calculated for middlemen, hoteliers or exporters, since no complete frame existed, and '
  'snowball sampling may over-represent those with stronger trading connections.',
 'No conventional response rate could be calculated for middlemen,': None,

 'A pilot test with 18 respondents checked':
  'A pilot test with 18 respondents checked whether the questionnaire items were clear, '
  'relevant and workable (Lowe, 2019), and informed the wording and sequencing of the tool.',

 'Data were collected from May 2022 to December 2023':
  'Data were collected from May 2022 to December 2023 using structured questionnaires, field '
  'observations and key-informant interviews. For Objective One the questionnaire recorded '
  'actor category, age, sex, marital status, education, household size, experience, income, '
  'ownership, scale, collective membership, credit and licensing. For Objective Two it '
  'recorded sourcing methods, volumes, grading, quality control, processing, preservation, '
  'packaging, transport, destinations, price setting, payment, technology use and market '
  'research, with field observation checking practices where they could be seen. For '
  'Objective Three it recorded operational and market constraints, infrastructure gaps, price '
  'risk, finance, institutional support, regulation and the opportunities respondents saw. '
  'Key informants gave context used to interpret the findings.',
 'For Objective Two, respondents described sourcing methods, volumes,': None,

 'Objective One was analysed with frequencies, valid percentages':
  'Objective One was analysed with frequencies, valid percentages and actor-specific BMU '
  'cross-tabulations, with chi-square tests for fishers and middlemen; Objective Two used the '
  'same summaries plus means, medians, quartiles and ranges for income and prices; Objective '
  'Three used frequencies, percentages and selected BMU associations. Hoteliers and exporters '
  'were described by actor category, their samples being too small for BMU tests.',

 'Questionnaires were administered on smartphones using KoBoToolbox':
  'Questionnaires were administered on smartphones using KoBoToolbox and KoBo Collect, and '
  'records were reviewed, coded and downloaded. Validation rules reduced missing and '
  'out-of-range responses, so cleaning focused on labels, coding consistency and duplicates.',

 'Categorical variables were summarised using frequencies and valid percentages':
  'Categorical variables were summarised using frequencies and valid percentages within actor '
  'category, continuous variables using the mean, standard deviation, median, quartiles, '
  'minimum and maximum. Every table in Chapter Four carries all four actor categories. '
  'Fishers and middlemen were additionally cross-tabulated by site; hoteliers and exporters '
  'were not.',

 'Chi-square tests assessed associations between BMU':
  'Chi-square tests assessed associations between BMU and selected categorical variables, '
  'separately for fishers and middlemen, with hoteliers and exporters excluded for small '
  'numbers and uneven coverage. Because many tables held small expected counts, two-sided '
  'Monte Carlo p-values based on 10,000 samples are reported with 99% confidence intervals, '
  'at alpha = .05.',
 'The tests covered objective-linked demographic, business, functional,': None,

 'Reported mud crab prices were compared with the Kruskal–Wallis H test':
  'Reported prices were compared with the Kruskal–Wallis H test, a rank-based alternative to '
  'one-way analysis of variance, chosen because the distributions were not normal and the '
  'groups very unequal, the smallest holding four and five observations. Three sets of '
  'comparisons were run, one per size grade: price across the four actor categories, fisher '
  'price across the four sites, and middleman price across the three sites where traders were '
  'sampled, at alpha = .05. Because no transaction-level costs, volumes or mortality were '
  'recorded, price differences between nodes are reported as gross marketing margins and '
  'shares of the end-of-chain price, never as profit.',
 'Three sets of comparisons were run, one per size grade:': None,

 'Four measures summarise market structure.':
  'Four measures summarise market structure. Concentration at first sale is taken over the '
  'buying points fishers named, using the concentration ratio and the Herfindahl-Hirschman '
  'Index, the sum of squared shares on a scale to 10,000, with 10,000 divided by that index '
  'giving the numbers-equivalent; because the survey recorded where fishers sold rather than '
  'what each buyer handled, these are shares of harvesters. The gross marketing margin at a '
  'node is that actor’s selling price less his buying price as a percentage of his selling '
  'price, the total applies the same formula across the chain, and the producer’s share is '
  'the fisher mean divided by the final-node mean, reported also net of measured mortality. '
  'Price dispersion is the coefficient of variation. The formulas are in the syntax file.',

 'The study adhered to ethical standards for statistical research.':
  'The study adhered to ethical standards for statistical research. Respondents were '
  'interviewed on attaining the legal age of 18, with consent from parents or guardians for '
  'those under 18; anonymity and confidentiality were maintained, participation was voluntary '
  'with the option to withdraw, and an ethical review certificate was obtained before data '
  'collection.',
}

done, deleted = set(), 0
for p in list(d.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    for opener, new in EDITS.items():
        if opener in done or not t.startswith(opener):
            continue
        if new is None:
            p._p.getparent().remove(p._p)
            deleted += 1
        else:
            retext(p, new)
        done.add(opener)
        break

missing = [o[:60] for o in EDITS if o not in done]
if missing:
    print('NOT FOUND, nothing saved:')
    for m in missing:
        print('   ', m)
    raise SystemExit(1)

d.save(DOC)
print(f'Chapter Two, third pass: {len(done)} paragraphs edited, {deleted} merged away')
