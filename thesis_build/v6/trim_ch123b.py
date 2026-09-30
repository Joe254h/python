# -*- coding: utf-8 -*-
"""Second, deeper pass over Chapters One to Three.

Chapter Four is left untouched by instruction, so the reduction has to come
from the other chapters. Every citation, every objective and every research
question is kept; the literature review keeps each of its claims but states
them once. Section 2.6.6 also had one sentence printed twice, which is repaired
here.
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
 # =============================================== Chapter One
 'Mud crabs (Scylla spp.), including Scylla serrata, are high-value':
  'Mud crabs (Scylla spp.), including Scylla serrata, are high-value crustaceans traded in '
  'tropical and subtropical regions, and much of the supply still depends on wild stocks, '
  'wild-caught juveniles and mangrove habitats. Across the Western Indian Ocean artisanal '
  'fishers harvest them in nearshore mangroves, on foot or from small canoes, and '
  'commercialisation has linked those fishers to traders, hotels and export markets. Those '
  'links create income but also decide who has market information, who sets grades and '
  'prices, and who bears the cost of keeping crabs alive.',
 'Across the Western Indian Ocean, artisanal fishers harvest mud crabs': None,

 'On the Kenyan coast, Scylla serrata is one of the commercially important':
  'On the Kenyan coast, Scylla serrata is one of the commercially important crustaceans '
  'available to small-scale fishers with little equipment. Demand from hotels, local markets '
  'and export buyers has raised its value, while reports of smaller crabs and the capture of '
  'immature animals suggest pressure on stocks and mangrove habitats. Kenyan research has '
  'examined the biology and ecology of mud crabs more closely than their markets, yet fishers '
  'also respond to the prices buyers offer, the grades buyers apply, transport, credit and '
  'payment terms. Where those conditions are poorly understood, management may address '
  'harvesting without addressing the incentives behind it.',

 'The trade connects fishers, brokers, traders, retailers, hoteliers, exporters':
  'The trade connects fishers, brokers, traders, retailers, hoteliers, exporters and '
  'consumers through grading, pricing, storage, transport, packaging and credit, and because '
  'crabs are sold alive their value depends on size, condition and survival. Kwale County '
  'supports active harvesting in mangrove creeks and supplies traders, hotels and export '
  'markets, yet there is limited evidence on the roles of different actors, how grades and '
  'prices are set, how crabs are transported and packaged, the payment arrangements used, '
  'and the constraints at each node. This study addresses that gap.',
 'Kenya’s Blue Economy agenda has renewed interest in mud crabs as a source': None,
 'Kwale County supports active mud crab harvesting in mangrove creeks': None,

 'Mud crab fishing on Kenya’s South Coast contributes to livelihoods':
  'Mud crab fishing on Kenya’s South Coast contributes to livelihoods and food security, but '
  'the marketing system is not well documented, and demand from local, tourism-linked and '
  'export markets has grown alongside concern about pressure on the resource (Fondo et al., '
  '2020; Mirera, 2017a; Fondo & Ogutu, 2021). Previous studies have concentrated on biology, '
  'ecology, production and aquaculture (Mirera, 2014a; Mirera, 2017a), leaving little '
  'evidence on how actor characteristics vary with market roles, access to buyers, '
  'collective organisation, credit, payment terms and bargaining conditions.',
 'Previous studies have concentrated on mud crab biology, ecology, production': None,

 'Available studies point to unstable prices, weak market links':
  'Available studies point to unstable prices, weak market links, limited participation in '
  'organised groups and uneven management support (Mirera, 2014a; Fondo & Ogutu, 2021), '
  'conditions that may restrict income and reinforce harvesting pressure when demand is met '
  'from wild stocks (FAO, 2025). The practical problem is an evidence gap: without an account '
  'of market structure, actor functions and the constraints at each node, interventions may '
  'address one part of the chain while leaving the trading conditions unchanged.',
 'The practical problem is therefore an evidence gap.': None,

 'The study documents a part of the South Coast mud crab fishery':
  'The study documents a part of the South Coast mud crab fishery that is often discussed but '
  'rarely measured: the organisation of exchange between harvesters, traders and downstream '
  'buyers. It connects actor profiles with grading, pricing, transport, packaging and payment '
  'practices, and identifies where respondents reported limited market access, post-harvest '
  'loss, weak infrastructure or gaps in institutional support.',
 'The analysis connects actor profiles with grading, pricing, transport': None,

 'For fishers and traders, the results provide a basis for clearer grades':
  'For fishers and traders the results give a basis for clearer grades, more transparent '
  'prices and better live-crab handling. For BMUs, county officers and national fisheries '
  'agencies they offer actor-specific evidence for licensing support, training, '
  'infrastructure planning and communication about management measures, although the '
  'cross-sectional data show where interventions can be tested rather than establishing '
  'causal effects. The study also records opportunities for women and young people in '
  'processing, hospitality procurement, trade and crab fattening, and adds a South Coast case '
  'to the limited literature on small-scale fishery markets in the Western Indian Ocean.',
 'The study also records opportunities for women and young people': None,

 # =============================================== Chapter Two
 'The genus Scylla contains four recognised mud crab species':
  'The genus Scylla contains four recognised mud crab species: S. serrata, S. tranquebarica, '
  'S. olivacea and S. paramamosain (Ogawa et al., 2011), occurring in mangrove estuaries and '
  'coastal waters of the Indian and Pacific oceans. Scylla serrata grows by moulting, with '
  'cultured crabs of 33-76 g recording daily gains of 0.68-1.58 g and adults exceeding 2 kg '
  'and 250 mm carapace width (Webley, 2008). Females migrate offshore to spawn, and the '
  'species is a benthic predator of slow-moving crustaceans, gastropods and molluscs, and '
  'cannibalistic (Allan & Fielder, 2003).',

 'Fishing grounds and capture methods vary with the target crab':
  'Fishing grounds and capture methods vary with the target crab, habitat, tide, gear and the '
  'fisher’s experience (Mirera, 2017a). Reported methods include hand collection, hooks and '
  'sticks, baited pots or traps, scoop or seine nets and hooked metal rods (Richmond et al., '
  '2006; Bonine et al., 2008). Kenyan fishers commonly remove crabs from mangrove burrows '
  'around low spring tides, taking market-sized animals for sale and smaller ones for culture '
  '(Moser et al., 2005).',

 'Along the Kenyan coast, many mud crab fishers work on foot in mangroves':
  'Many work on foot and rely on knowledge of burrows and tidal creeks rather than '
  'specialised equipment (Fondo et al., 2020; Mirera et al., 2013), holding catches at home '
  'for several days until enough have accumulated for sale (Ochiewo et al., 2010), which '
  'makes survival and handling part of the marketing problem. The Fisheries Management and '
  'Development Act, 2016 provides for designated landing and management arrangements, but mud '
  'crab fishers do not always use formal landing sites or licences, so catches may stay '
  'outside routine landing records.',
 'The Fisheries Management and Development Act, 2016 provides for designated': None,

 'Scylla serrata is among the more valuable shellfish harvested from tropical':
  'Scylla serrata is among the more valuable shellfish harvested from tropical mangroves, and '
  'on Kenya’s South Coast the fishery gives cash income to coastal households and connects '
  'small-scale harvesters with traders and downstream buyers; its commercial growth has '
  'created a longer market chain rather than replacing small-scale production (FAO, 2025). '
  'Demand for live crabs raises both harvesting pressure and the value of keeping crabs '
  'alive, and evidence from the region suggests that buyer concentration, grade setting and '
  'market access shape prices and the distribution of gross returns (Jacinto, 2004; Crona et '
  'al., 2016).',
 'Demand for live crabs can increase both harvesting pressure': None,

 'The mud crab fishery involves fishers, brokers or middlemen, traders':
  'The fishery involves fishers, brokers or middlemen, traders, wholesalers, retailers and '
  'final buyers. Fishers are typically small-scale operators who depend on mangrove habitats '
  'and use hand collection or simple gear (Mirera et al., 2013); the others aggregate, grade, '
  'transport, process or sell the catch.',

 'Participation differs by age, experience, education, gender and access':
  'Participation differs by age, experience, education, gender and access to finance. Along '
  'the Kenyan coast harvesting and formal leadership have been largely male-dominated, with '
  'women more visible in trade, processing and crab fattening (Ochiewo et al., 2010; Mirera, '
  '2014a). Earlier studies place many Kenyan crab fishers between 23 and 55 years of age and '
  'report primary education as far more common than secondary among East African crab fishers '
  '(Fulanda et al., 2009; Ndanga et al., 2013). That context does not show whether actor '
  'profiles are the same across BMUs or market nodes.',

 'Functions change as crabs move through the chain.':
  'Functions change as crabs move through the chain. Fishers capture crabs by hand, from '
  'burrows or with baited gear, and the method affects size, condition and survival, which '
  'bear on the price at first sale (Sultana et al., 2018). Middlemen buy at landing sites or '
  'villages, combine catches, grade and arrange holding and transport; their networks connect '
  'fishers to distant buyers but may also give them an information and bargaining advantage '
  'where fishers have few outlets.',
 'Middlemen buy from landing sites or villages, combine catches': None,

 'Wholesalers, retailers, hotels, restaurants and exporters place greater':
  'Wholesalers, retailers, hotels, restaurants and exporters emphasise consistent quality and '
  'survival, especially where crabs are traded alive (FAO, 2025), so the chain is better '
  'examined as a sequence of distinct functions than as a single group of traders.',

 'Mud crab trade depends on keeping a live, perishable product':
  'Mud crab trade depends on keeping a live, perishable product in saleable condition, so '
  'grading, price setting, transport, packaging and payment are part of production economics '
  'rather than secondary activities (FAO, 2025). They distribute opportunity and risk '
  'together: whoever controls grading or transport may reach a higher-value buyer, and '
  'whoever holds live crabs bears the mortality, the delayed payment and the rejected '
  'consignment.',
 'These practices distribute both opportunity and risk.': None,

 'Crabs are commonly graded by size, weight, sex, shell hardness':
  'Crabs are commonly graded by size, weight, sex, shell hardness and physical condition. '
  'Large hard-shell crabs are preferred because they carry more meat and travel better, males '
  'may command higher prices, and trade in berried females may be restricted for conservation '
  '(FAO, 2025).',

 'Grading may occur at the landing site or after a middleman':
  'Grading may happen at the landing site or after a middleman has aggregated several '
  'catches. Where the criteria are informal or applied visually, a fisher may be unable to '
  'verify why a crab was placed in a particular grade. The issue is not grading itself, which '
  'can reflect real quality differences, but whether the criteria and their price '
  'consequences are transparent.',

 'Mud crab prices vary with grade, season, demand, distance to market':
  'Mud crab prices vary with grade, season, demand, distance to market and whether crabs are '
  'sold alive, with large live crabs generally receiving more in urban, hotel and export '
  'markets (FAO, 2025).',

 'Small-scale fishers may accept a buyer’s price when they lack holding':
  'Small-scale fishers may accept a buyer’s price when they lack holding facilities, need '
  'cash immediately or depend on that buyer for transport and credit. Informal agreements can '
  'cut transaction costs but can also make the basis of a price hard to challenge (Crona et '
  'al., 2016), which makes buyer choice and independent market information matter alongside '
  'the nominal price.',

 'Transport affects both survival and quality.':
  'Transport affects survival and quality. Live mud crabs are vulnerable to heat, dehydration '
  'and handling stress, and deaths in transit reduce what can be sold, so traders use '
  'baskets, plastic crates or wooden boxes, often with damp material.',

 'Long distances, poor roads and limited cold-chain or live-holding':
  'Long distances, poor roads and limited cold-chain or live-holding facilities add to that '
  'risk in the Western Indian Ocean. Shorter journeys and better containment may cut '
  'mortality without increasing fishing effort; the question is which actors have access to '
  'those options and who pays for them.',

 'Packaging controls movement, moisture and physical damage':
  'Packaging controls movement, moisture and physical damage in transit. Live crabs may be '
  'tied or separated to reduce injury and cannibalism, and containers must ventilate and '
  'protect claws and legs, which affect market acceptance.',

 'Export markets often require consistent packaging, labels and traceability.':
  'Export markets often require consistent packaging, labels and traceability, while '
  'small-scale traders use low-cost local materials. The trade-off between container cost, '
  'survival and reusability should be assessed under normal trading conditions rather than '
  'assumed.',

 'Cash remains common at landing sites because fishers need immediate income.':
  'Cash remains common at landing sites because fishers need immediate income, though payment '
  'may be delayed until a broker has sold the crabs, especially where the broker provides '
  'transport or holding (Crona et al., 2016).',

 'Buyers may advance cash or gear in return for continued or exclusive supply.':
  'Buyers may also advance cash or gear in return for continued or exclusive supply, an '
  'arrangement Crona et al. (2016) describe as solving a short-term financing problem while '
  'narrowing the seller’s choice of buyer. Whether mobile money changes that balance in this '
  'fishery is an empirical question taken up in Chapter Four.',

 'Mud crab actors face ecological, operational and market constraints.':
  'Mud crab actors face ecological, operational and market constraints. Fishers report '
  'seasonal availability and declining catches where juvenile or berried crabs are harvested '
  'and mangroves are degraded (Mirera, 2017a), while traders must keep live crabs saleable '
  'while assembling volume.',

 'Limited credit, unstable prices, inadequate holding facilities':
  'Limited credit, unstable prices, inadequate holding facilities and dependence on a few '
  'brokers reduce bargaining options, and weak enforcement of size or harvest rules may let '
  'short-term demand undermine the resource the trade depends on (Mirera, 2017a).',

 'Demand for large, healthy crabs creates room for better handling':
  'Demand for large, healthy crabs leaves room for better handling, clearer grades and '
  'higher-value products. Crab fattening can raise sale weight, though its value depends on '
  'survival, feed, labour, seed sourcing and a confirmed buyer (Mirera, 2014b).',

 'Community participation in size limits and temporary closures':
  'Community participation in size limits and temporary closures has improved awareness and '
  'product quality in co-managed small-scale fisheries (Gutiérrez et al., 2011). The lesson '
  'for Kenya is not that the same measure transfers unchanged, but that market incentives and '
  'local enforcement need designing together.',

 'The Fisheries Management and Development Act, No. 35 of 2016 (Cap. 378) provides':
  'The Fisheries Management and Development Act, No. 35 of 2016 (Cap. 378) is the main '
  'national framework for conservation, management and development of fisheries resources, '
  'including crustaceans, and recognises small-scale fisheries and co-management through '
  'Beach Management Units. Governance is shared between national and county institutions, '
  'counties developing management plans while the national government coordinates, which '
  'matters for a fishery rooted in mangrove habitats and local landing sites.',
 'Fisheries governance is shared between national and county institutions.': None,

 'The Fisheries Management and Development (Safety and Quality) Regulations, 2024':
  'The Fisheries Management and Development (Safety and Quality) Regulations, 2024 address '
  'the handling, movement and marketing of fishery products, and their licensing, '
  'traceability, hygiene and quality requirements bear directly on traders and exporters '
  'seeking formal markets. Kenya’s Blue Economy and sustainable-development commitments add '
  'emphasis on traceability, monitoring and value-chain development (Fondo & Ogutu, 2021), '
  'where the practical gaps for small-scale actors remain awareness, compliance support and '
  'consistent enforcement.',
 'Kenya’s Blue Economy and sustainable-development commitments place greater': None,

 'The sections above summarise what previous studies have reported.':
  'This section asks where those studies agree, where they conflict, what their methods can '
  'support, and what remains unanswered for the South Coast.',

 'Three findings recur across settings and methods':
  'Three findings recur across settings and methods and can be treated as reasonably secure. '
  'Mud crab chains in the Western Indian Ocean are a sequence of distinct functions rather '
  'than a single trading group, with harvesting, aggregation, processing and export performed '
  'by different actors (Mirera, 2017a; Jacinto, 2004; FAO, 2025). Survival of a live, '
  'perishable product governs value, so handling, containment and holding time are production '
  'economics (Mirera et al., 2013). And small-scale harvesters in the region work with '
  'limited finance, organisation and access to formal markets (Béné et al., 2007; Fondo & '
  'Ogutu, 2021). This study tests all three against a single dataset.',

 'The clearest disagreement in this literature is whether middlemen':
  'The clearest disagreement is whether middlemen improve or reduce the position of fishers. '
  'One line treats the middleman as a net cost: Jacinto (2004) argues that the share of final '
  'value captured at each node follows control of information and market access rather than '
  'physical effort, so an actor between the harvester and the buyer captures value the '
  'harvester cannot reach, and Béné et al. (2007) extend this to credit, treating an advance '
  'against future supply as a mechanism of persistent low returns.',
 'One line of work treats the middleman as a net cost to the harvester.': None,

 'A second line reaches almost the opposite conclusion.':
  'A second line reaches almost the opposite conclusion. Crona et al. (2016), working in '
  'Kenya and Zanzibar, describe middlemen as a critical social-ecological link whose '
  'relational knowledge is not easily replaced, blamed for outcomes settled further along the '
  'chain while operating on modest turnovers and carrying the mortality risk. On that reading '
  'removing the middleman would not transfer their margin to the fisher.',

 'The two positions are not reconcilable at the level of assertion':
  'The two make different empirical claims, one about who captures the value and one about '
  'what the middleman’s position returns once risk is counted, so resolving them needs the '
  'price at each node and the share each node holds in the same chain. No study reports that '
  'for a Kenyan mud crab chain, which is the first gap this study addresses.',

 'A second, less openly stated disagreement concerns grading.':
  'A second disagreement concerns grading. FAO (2025) treats grading by size, weight, shell '
  'condition and claw size as a legitimate quality signal; Jacinto (2004) treats the same '
  'practice as informational asymmetry, because a criterion the buyer applies and the seller '
  'cannot verify transfers value rather than signalling it. Both may hold, but only if the '
  'rule is applied consistently and both parties can read it, which means recording the '
  'criteria each actor category actually uses.',

 'Four limitations recur in the work reviewed above.':
  'Four limitations recur in the work reviewed above. The first is a production focus: much '
  'of the Kenyan mud crab literature is biological, ecological or aquacultural (Mirera, '
  '2017a, 2017b; Mirera & Mosknes, 2015; Moser et al., 2005; Webley, 2008), careful within '
  'its own terms but not designed to describe exchange, so it cannot be read as evidence '
  'about prices, margins or bargaining.',

 'The second is a setting mismatch.':
  'The second is a setting mismatch: where organisation and training have been studied, the '
  'setting has often been organised community aquaculture groups rather than independent '
  'capture-fishery actors (Mirera, 2014a), and what groups achieve there should not be '
  'transferred to a capture fishery where no group exists at all.',

 'The third is aggregation.':
  'The third is aggregation: regional and national assessments describe constraints in '
  'finance, organisation and market access at sector level (Fondo & Ogutu, 2021; Béné et al., '
  '2007), so they cannot say which actor category faces which constraint, or where an '
  'intervention should be aimed.',

 'The fourth is the absence of cost data':
  'The fourth is the absence of cost data, which this study shares. Munga and Muthumbi (2018) '
  'show for the Tana Delta that gross price differentials narrow considerably once handling '
  'and transport are netted out, so any study reporting gross prices must stop short of '
  'claims about profit, and Section 5.6 states which dimensions that rules out.',

 'The literature specific to this coast is thinner than the regional':
  'The literature specific to this coast is thinner and weighted towards production. Mirera '
  'et al. (2013) document fishing tactics and traditional knowledge, including holding crabs '
  'at home until enough accumulate for sale. Ochiewo et al. (2010) and Mirera (2014a) record '
  'the gendered division of the fishery, harvesting and first-tier trade male-dominated and '
  'women more visible in processing and trade. Fondo et al. (2020) describe the national '
  'status of the fishery and Fondo and Ogutu (2021) place it within the Blue Economy agenda, '
  'while Fulanda et al. (2009) and Kimani et al. (2018) supply the fisher population figures '
  'on which this study’s sampling frame rests.',

 'Kwale County itself appears in this literature mainly as a location':
  'Kwale County appears mainly as a location rather than a subject. Njiru et al. (2021) treat '
  'its institutions directly, finding that trader participation in Beach Management Units '
  'varies with the trader’s own circumstances, which supports communication designed for '
  'particular actor groups. Beyond that, Shimoni, Majoreni, Vanga and Msambweni are largely '
  'undocumented as markets rather than as landing sites.',

 'Three things follow. Prices at each node in a Kwale mud crab chain':
  'So prices at each node in a Kwale mud crab chain have not been reported, the grading '
  'criteria each actor category uses have not been recorded, and no study has tested whether '
  'actor characteristics, functions or constraints differ between the BMUs of this coast.',

 'The gap this study addresses is specific rather than general.':
  'The gap is specific. Previous work establishes that mud crab chains are functionally '
  'differentiated, that survival governs value and that small-scale harvesters are '
  'institutionally weak. It does not establish how the value of a South Coast mud crab is '
  'divided between the people who catch, trade and sell it, whether the grading rule behind '
  'that division is shared or asymmetric, or whether any of it varies between the Beach '
  'Management Units. Those three questions are the three objectives of this study.',

 'This study uses the Structure-Conduct-Performance (SCP) paradigm':
  'This study uses the Structure-Conduct-Performance (SCP) paradigm as its main analytical '
  'framework. SCP is commonly applied in agricultural and fisheries marketing to organise '
  'evidence on market structure, actor conduct and market outcomes, and here it connects the '
  'composition and organisation of the mud crab market with the practices observed at each '
  'node. It guides interpretation and is not used to claim a causal sequence.',

 'Market structure is described through the number and types of actors':
  'Market structure is described through the number and types of actors, their '
  'characteristics, entry conditions, licensing, access to capital, collective organisation '
  'and buyer connections; conduct covers sourcing, grading, handling, pricing, payment, '
  'transport and credit; performance is considered through the descriptive indicators the '
  'dataset holds, namely reported income and prices, market access, mortality or spoilage and '
  'perceptions of market organisation.',

 'Value-chain concepts are used as a mapping device':
  'Value-chain concepts map crabs from harvesting through aggregation, hospitality and '
  'export, not as a second causal theory, and the sustainable livelihoods framework of '
  'Allison and Ellis (2001) gives background for reading education, experience, finance and '
  'collective membership, though no complete set of livelihood assets was measured.',

 'Figure 3 organises the study variables by objective':
  'Figure 3 organises the study variables by objective and shows how they were used. It is a '
  'descriptive framework, not a causal model: the arrows indicate the order in which market '
  'structure, actor conduct and observed outcomes were examined, not estimated effects.',

 'Objective One describes market structure and actor profiles using actor category':
  'Objective One describes market structure and actor profiles using actor category, BMU, '
  'age, gender, education, experience, scale, licensing, collective membership and credit, '
  'summarised by actor category and compared across BMUs where coverage allowed. Objective '
  'Two examines conduct and functions at each node: sourcing, grading, handling, packaging, '
  'transport, pricing, payment, buyer relations and market research, with income, prices, '
  'market access and losses reported as descriptive outcomes rather than a performance index. '
  'Objective Three describes the infrastructure, market barriers, policy awareness, risks and '
  'opportunities each actor category reported. No mediation or moderation model was '
  'estimated, and actor category and BMU serve as grouping variables.',
 'Objective Three describes the infrastructure, market barriers, policy awareness': None,

 # =============================================== Chapter Three
 'This chapter describes the study design, site, target population':
  'This chapter describes the study design, site, target population, sampling, data '
  'collection and analysis, chosen to describe the actors, functions, constraints and '
  'opportunities in the Kwale County mud crab market and to compare categorical variables '
  'across BMUs where the sample allowed.',

 'The study was conducted on the South Coast of Kenya, mainly in Kwale County':
  'The study was conducted on the South Coast of Kenya, mainly in Kwale County, between '
  'latitudes 3.05 degrees and 4.75 degrees South and longitudes 38.52 degrees and 39.51 '
  'degrees East (Figure 4). The county covers about 8,270.2 square kilometres from Likoni to '
  'Vanga, where mangrove forests, tidal creeks and shallow coastal waters provide breeding, '
  'feeding and shelter habitat for Scylla serrata (Mirera, 2017a; Fondo et al., 2020). It was '
  'selected as an established harvesting and trading area where small-scale fishers reach the '
  'mangroves on foot or by canoe and year-round access makes crab fishing an important source '
  'of cash.',

 'The county has 20 Beach Management Units (BMUs) and 54 landing sites':
  'The county has 20 Beach Management Units and 54 landing sites, which regulate fishing, '
  'manage landing sites and promote sustainable use, and are therefore the entry points for '
  'understanding local harvesting and marketing (Njiru et al., 2021). Landing sites are where '
  'fishers sell to brokers and traders, which makes them the right places to collect data on '
  'grading, pricing, transport, packaging and payment. Tourism and urban markets generate '
  'high demand for live crabs, drawing multiple actors into the chain (FAO, 2025), so the '
  'fishery here has shifted from subsistence towards a market-oriented activity.',
 'The South Coast is also strongly influenced by tourism and urban markets': None,

 'The study used a cross-sectional descriptive mixed-methods design.':
  'The study used a cross-sectional descriptive mixed-methods design. Each respondent was '
  'surveyed once, with field observations and key-informant interviews supplying context on '
  'handling, institutions and market relationships. It supports actor profiles, comparisons '
  'among actor categories and exploratory BMU associations, but establishes no causal '
  'pathway and no seasonal change.',

 # fix_refs.py runs later and swaps the opening sentence for one that carries
 # the Lamm and Lamm (2019) definition, so that sentence is left word for word
 'The target population comprised mud crab fishers':
  'The target population comprised mud crab fishers, middlemen, hoteliers and exporters '
  'operating in Kwale County. These groups were selected because they harvest, handle, '
  'aggregate, process or trade mud crabs and so correspond to the three objectives. '
  'Consumers, restaurants that did not procure directly, input suppliers and other service '
  'providers were outside the survey scope, so the study cannot describe consumer '
  'preferences or the full set of supporting services. Ministry of Fisheries records '
  'informed the fisher sampling frame; complete lists did not exist for the other three '
  'groups, whose accessible population depended on referrals and availability.',

 'The completed survey covered 96 actors: 65 mud crab fishers':
  'The completed survey covered 96 actors: 65 fishers, 22 middlemen, five hoteliers and four '
  'exporters. Fishers were recruited from the selected BMUs using the available frame; '
  'because no complete lists of downstream actors existed, respondents identified traders and '
  'buyers who could be approached, and those referrals were followed through snowball '
  'sampling.',

 'The study reached 65 of the target 83 fishers':
  'The study reached 65 of the target 83 fishers, 78.3%, the shortfall arising mainly because '
  'some fishers moved among landing sites and were absent during scheduled visits. The '
  'achieved sample is adequate for a descriptive account of the respondents reached, but the '
  'missing 18 may differ from those interviewed, so site-level percentages for BMUs with few '
  'respondents should be read cautiously.',

 'A conventional response rate could not be calculated for middlemen':
  'No conventional response rate could be calculated for middlemen, hoteliers or exporters, '
  'since no complete frame existed. Snowball sampling was practical for locating dispersed '
  'actors but may over-represent those with stronger trading connections, and the small '
  'hotelier and exporter samples and the absence of middlemen at some BMUs limit '
  'generalisation beyond the surveyed actors.',

 'A pilot test involving 18 respondents was used to check':
  'A pilot test with 18 respondents checked whether the questionnaire items were clear, '
  'relevant and workable in the field (Lowe, 2019), and its feedback informed the wording and '
  'sequencing of the tool.',

 'Data were collected from May 2022 to December 2023':
  'Data were collected from May 2022 to December 2023 using structured questionnaires, field '
  'observations and key-informant interviews. For Objective One the questionnaire recorded '
  'actor category, age, sex, marital status, education, household size, experience, monthly '
  'income, business ownership, scale, collective membership, credit, licensing and '
  'institutional affiliation.',
 'For Objective One, the questionnaire recorded actor category, age, sex': None,

 'For Objective Two, respondents described their harvesting or sourcing methods':
  'For Objective Two, respondents described sourcing methods, volumes, grading, quality '
  'control, processing, preservation, packaging, transport, market destinations, price '
  'setting, payment, technology use, market research and sources of technical knowledge, with '
  'field observation checking handling, grading, transport and marketing where they could be '
  'seen. For Objective Three they identified operational and market constraints, '
  'infrastructure gaps, price risk, access to finance, technology, institutional support, '
  'regulation and capacity needs, and the opportunities they saw. Key informants, including '
  'BMU leaders and government officers, gave context used to interpret the survey findings '
  'rather than as a separate causal test.',
 'For Objective Three, respondents identified operational and market constraints': None,

 'Secondary evidence came from published studies, government reports':
  'Secondary evidence came from published studies and government reports on mud crab '
  'fisheries, actor roles and market conditions.',

 'Objective One was analysed with frequencies, valid percentages':
  'Objective One was analysed with frequencies, valid percentages and actor-specific BMU '
  'cross-tabulations, with chi-square tests for selected categorical variables among fishers '
  'and middlemen. Objective Two used the same summaries for functions and market practices, '
  'with means, medians, quartiles and ranges for income and prices. Objective Three used '
  'frequencies, percentages and selected BMU associations. Hoteliers and exporters were '
  'described by actor category, their samples being too small and uneven for BMU tests.',

 'Questionnaires were administered on smartphones using KoBoToolbox':
  'Questionnaires were administered on smartphones using KoBoToolbox and KoBo Collect, and '
  'records were reviewed, coded and downloaded in CSV and XLSX. Validation rules in the form '
  'reduced missing and out-of-range responses, so cleaning focused on labels, coding '
  'consistency, duplicate checks and comparison with the original records where a value '
  'looked unusual.',
 'Validation rules in the KoBo form reduced missing and out-of-range responses.': None,

 'After cleaning, the dataset was imported into IBM SPSS Statistics.':
  'The dataset was then imported into IBM SPSS Statistics, variables labelled by objective '
  'and checked against the questionnaire.',

 'Descriptive analysis was conducted in IBM SPSS Statistics.':
  'Categorical variables were summarised using frequencies and valid percentages within actor '
  'category; continuous variables, including reported monthly income and mud crab prices, '
  'using the mean, standard deviation, median, quartiles, minimum and maximum. Every table in '
  'Chapter Four carries all four actor categories so the positions can be compared on one '
  'row. Fishers and middlemen were additionally cross-tabulated by site; hoteliers and '
  'exporters were not, their samples being small and their site coverage uneven. All charts '
  'came from the same dataset.',

 'Chi-square tests were used to assess associations between BMU':
  'Chi-square tests assessed associations between BMU and selected categorical variables, '
  'separately for fishers and middlemen, since their functions and distributions differed '
  'across sites. Hoteliers and exporters were excluded from BMU testing for small numbers and '
  'uneven coverage.',

 'The tests covered objective-linked demographic, business, functional':
  'The tests covered objective-linked demographic, business, functional, market and '
  'constraint variables. Because many contingency tables held small expected counts, '
  'two-sided Monte Carlo p-values based on 10,000 samples are reported with 99% confidence '
  'intervals, at alpha = .05.',

 'Reported mud crab prices were compared with the Kruskal–Wallis H test':
  'Reported mud crab prices were compared with the Kruskal–Wallis H test, a rank-based '
  'alternative to one-way analysis of variance, chosen because the price distributions were '
  'not normal, the actor groups very unequal in size and the smallest held four and five '
  'observations, conditions under which a parametric test would not be dependable.',

 'Three sets of comparisons were run, one per size grade.':
  'Three sets of comparisons were run, one per size grade: price across the four actor '
  'categories, fisher price across the four sites, and middleman price across the three sites '
  'where traders were sampled, at alpha = .05. Because the survey recorded no '
  'transaction-level costs, volumes or mortality, price differences between nodes are '
  'reported as gross marketing margins and shares of the end-of-chain price, never as profit.',

 'Four measures summarise market structure.':
  'Four measures summarise market structure. Concentration at first sale is taken over the '
  'buying points fishers named, using the concentration ratio and the Herfindahl-Hirschman '
  'Index, the sum of the squared shares on a scale to 10,000; dividing 10,000 by that index '
  'gives the numbers-equivalent. Because the survey recorded where fishers sold rather than '
  'what each buyer handled, these are shares of harvesters, not of volume. The gross '
  'marketing margin at a node is that actor’s selling price less his buying price as a '
  'percentage of his selling price, the total marketing margin applies the same formula '
  'across the chain, and the producer’s share is the fisher mean divided by the final-node '
  'mean, reported also net of the measured physical mortality. Price dispersion is the '
  'coefficient of variation. All were computed from the SPSS output, and the formulas are in '
  'the syntax file.',

 'The study adhered to ethical standards for statistical research.':
  'The study adhered to ethical standards for statistical research. Respondents were '
  'interviewed on attaining the legal age of 18, with consent sought from parents or '
  'guardians for those under 18. Anonymity and confidentiality were maintained, participation '
  'was voluntary with the option to withdraw, and an ethical review certificate was obtained '
  'before data collection.',
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

missing = [o[:58] for o in EDITS if o not in done]
if missing:
    print('NOT FOUND, nothing saved:')
    for m in missing:
        print('   ', m)
    raise SystemExit(1)

d.save(DOC)
print(f'Chapters One and Two, second pass: {len(done)} paragraphs edited, {deleted} merged away')
