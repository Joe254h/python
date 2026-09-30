# -*- coding: utf-8 -*-
"""Final pass on Chapters One, Two and Three.

The last of the reduction, taken from the introduction, the critical assessment
and the methods. Every citation is kept.
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
 # ---- Chapter One
 'On the Kenyan coast, Scylla serrata is one of the commercially important':
  'On the Kenyan coast, Scylla serrata is one of the commercially important crustaceans '
  'available to small-scale fishers with little equipment. Demand from hotels, local markets '
  'and export buyers has raised its value, while reports of smaller crabs and the capture of '
  'immature animals suggest pressure on stocks and mangrove habitats. Kenyan research has '
  'examined the biology and ecology of mud crabs more closely than their markets, yet fishers '
  'also respond to the prices buyers offer, the grades they apply, transport, credit and '
  'payment terms, so management may address harvesting without addressing the incentives '
  'behind it.',

 'The trade connects fishers, brokers, traders, retailers, hoteliers, exporters':
  'The trade connects fishers, brokers, traders, retailers, hoteliers, exporters and '
  'consumers through grading, pricing, storage, transport, packaging and credit, and because '
  'crabs are sold alive their value depends on size, condition and survival. Kwale County '
  'supports active harvesting and supplies traders, hotels and export markets, yet there is '
  'limited evidence on the roles of different actors, how grades and prices are set, how '
  'crabs are transported and packaged, the payment arrangements used, and the constraints at '
  'each node. This study addresses that gap.',

 'For fishers and traders the results give a basis for clearer grades':
  'For fishers and traders the results give a basis for clearer grades, more transparent '
  'prices and better live-crab handling; for BMUs, county officers and national agencies they '
  'offer actor-specific evidence for licensing support, training, infrastructure planning and '
  'communication about management measures, though the cross-sectional data show where '
  'interventions can be tested rather than establishing causal effects. The study also '
  'records opportunities for women and young people in processing, hospitality procurement, '
  'trade and crab fattening.',

 # ---- Chapter Two
 'Three findings recur and can be treated as reasonably secure.':
  'Three findings recur and can be treated as reasonably secure: mud crab chains in the '
  'region are a sequence of distinct functions rather than one trading group (Mirera, 2017a; '
  'Jacinto, 2004; FAO, 2025); survival of a live product governs value, so handling and '
  'holding time are production economics (Mirera et al., 2013); and small-scale harvesters '
  'work with limited finance, organisation and market access (Béné et al., 2007; Fondo & '
  'Ogutu, 2021).',

 'The clearest disagreement is whether middlemen improve or reduce':
  'The clearest disagreement is whether middlemen improve or reduce the position of fishers. '
  'Jacinto (2004) argues the share of final value captured at each node follows control of '
  'information and market access rather than physical effort, so an actor between harvester '
  'and buyer captures value the harvester cannot reach, and Béné et al. (2007) treat an '
  'advance against future supply as a mechanism of persistent low returns. Crona et al. '
  '(2016) reach almost the opposite conclusion, describing middlemen as a critical '
  'social-ecological link blamed for outcomes settled further along the chain while carrying '
  'the mortality risk.',

 'A second disagreement concerns grading.':
  'A second disagreement concerns grading. FAO (2025) treats it as a legitimate quality '
  'signal; Jacinto (2004) treats it as informational asymmetry, since a criterion the buyer '
  'applies and the seller cannot verify transfers value rather than signalling it. Both may '
  'hold, but only if the rule is applied consistently and both parties can read it.',

 'Objective One uses actor category, BMU, age, gender, education':
  'Objective One uses actor category, BMU, age, gender, education, experience, scale, '
  'licensing, collective membership and credit, summarised by actor category and compared '
  'across BMUs where coverage allowed. Objective Two examines conduct at each node: sourcing, '
  'grading, handling, packaging, transport, pricing, payment, buyer relations and market '
  'research, with income, prices, market access and losses as descriptive outcomes. Objective '
  'Three describes the infrastructure, market barriers, policy awareness, risks and '
  'opportunities each category reported.',

 # ---- Chapter Three
 'The study was conducted on the South Coast of Kenya, mainly in Kwale County':
  'The study was conducted on the South Coast of Kenya, mainly in Kwale County, between '
  'latitudes 3.05 and 4.75 degrees South and longitudes 38.52 and 39.51 degrees East (Figure '
  '4). The county covers about 8,270.2 square kilometres from Likoni to Vanga, where mangrove '
  'forests, tidal creeks and shallow waters provide habitat for Scylla serrata (Mirera, '
  '2017a; Fondo et al., 2020). Its 20 Beach Management Units and 54 landing sites are where '
  'fishers sell to brokers and traders (Njiru et al., 2021), which makes them the right '
  'places to collect data on grading, pricing, transport, packaging and payment, and tourism '
  'and urban markets generate high demand for live crabs (FAO, 2025).',

 'Data were collected from May 2022 to December 2023':
  'Data were collected from May 2022 to December 2023 using structured questionnaires, field '
  'observations and key-informant interviews. For Objective One the questionnaire recorded '
  'actor category, age, sex, marital status, education, household size, experience, income, '
  'ownership, scale, collective membership, credit and licensing. For Objective Two it '
  'recorded sourcing methods, volumes, grading, quality control, processing, preservation, '
  'packaging, transport, destinations, price setting, payment and market research, with field '
  'observation checking practices where they could be seen. For Objective Three it recorded '
  'operational and market constraints, infrastructure gaps, price risk, finance, '
  'institutional support, regulation and the opportunities respondents saw.',

 'Four measures summarise market structure.':
  'Four measures summarise market structure. Concentration at first sale is taken over the '
  'buying points fishers named, using the concentration ratio and the Herfindahl-Hirschman '
  'Index, the sum of squared shares on a scale to 10,000, which divided into 10,000 gives the '
  'numbers-equivalent; because the survey recorded where fishers sold rather than what each '
  'buyer handled, these are shares of harvesters. The gross marketing margin at a '
  'node is that actor’s selling price less his buying price as a percentage of his selling '
  'price, the total applies it across the chain, and the producer’s share is the fisher mean '
  'divided by the final-node mean, reported also net of measured mortality. Price dispersion '
  'is the coefficient of variation.',

 'Fishing grounds and capture methods vary with the target crab':
  'Fishing grounds and capture methods vary with the target crab, habitat, tide, gear and the '
  'fisher’s experience (Mirera, 2017a), and include hand collection, hooks and sticks, baited '
  'pots or traps, scoop or seine nets and hooked metal rods (Richmond et al., 2006; Bonine et '
  'al., 2008). Kenyan fishers work mainly on foot, taking crabs from mangrove burrows around '
  'low spring tides (Moser et al., 2005; Fondo et al., 2020; Mirera et al., 2013), and may '
  'hold catches at home until enough accumulate for sale (Ochiewo et al., 2010), which makes '
  'survival part of the marketing problem. They do not always use the landing sites or '
  'licences the Fisheries Management and Development Act, 2016 provides for.',

 'The fishery involves fishers, brokers or middlemen, traders':
  'The fishery involves fishers, brokers or middlemen, traders, wholesalers, retailers and '
  'final buyers: fishers are small-scale operators using hand collection or simple gear '
  '(Mirera et al., 2013), the others aggregate, grade, transport, process or sell. '
  'Participation differs by age, experience, education, gender and finance, with harvesting '
  'and formal leadership largely male-dominated and women more visible in trade, processing '
  'and crab fattening (Ochiewo et al., 2010; Mirera, 2014a). Earlier studies place many '
  'Kenyan crab fishers between 23 and 55 years of age and report primary education as far '
  'more common than secondary (Fulanda et al., 2009; Ndanga et al., 2013).',

 'The literature specific to this coast is thinner and weighted towards production.':
  'The literature specific to this coast is thinner and weighted towards production. Mirera '
  'et al. (2013) document fishing tactics and traditional knowledge; Ochiewo et al. (2010) '
  'and Mirera (2014a) record the gendered division of the fishery; Fondo et al. (2020) and '
  'Fondo and Ogutu (2021) describe its national status and place within the Blue Economy '
  'agenda; and Fulanda et al. (2009) and Kimani et al. (2018) supply the fisher population '
  'figures behind this sampling frame. Njiru et al. (2021) treat Kwale’s institutions '
  'directly, finding trader participation in Beach Management Units varies with the trader’s '
  'own circumstances.',

 'Reported prices were compared with the Kruskal–Wallis H test':
  'Reported prices were compared with the Kruskal–Wallis H test, a rank-based alternative to '
  'one-way analysis of variance, chosen because the distributions were not normal and the '
  'groups very unequal. Three sets of comparisons were run, one per size grade: price across '
  'the four actor categories, fisher price across the four sites, and middleman price across '
  'the three sites where traders were sampled, at alpha = .05. Because no transaction-level '
  'costs or volumes were recorded, price differences are reported as gross marketing margins '
  'and shares of the end-of-chain price, never as profit.',

 # this runs before fix_refs.py, which swaps the first sentence for one
 # carrying the Lamm and Lamm (2019) definition, so it stays word for word
 'The target population comprised mud crab fishers':
  'The target population comprised mud crab fishers, middlemen, hoteliers and exporters '
  'operating in Kwale County. These groups harvest, handle, aggregate, process or trade mud '
  'crabs. Consumers, restaurants that did not procure directly, input suppliers and other '
  'service providers were outside the survey scope. Ministry of Fisheries records informed '
  'the fisher sampling frame; complete lists did not exist for the other three groups.',

 'The Fisheries Management and Development Act, No. 35 of 2016 (Cap. 378) is the main':
  'The Fisheries Management and Development Act, No. 35 of 2016 (Cap. 378) is the main '
  'national framework for fisheries resources and recognises co-management through Beach '
  'Management Units, with governance shared between national and county institutions. The '
  'Fisheries Management and Development (Safety and Quality) Regulations, 2024 govern '
  'handling, movement and marketing, their licensing, traceability and quality requirements '
  'bearing on traders and exporters seeking formal markets, while Kenya’s Blue Economy '
  'commitments add emphasis on traceability and value-chain development (Fondo & Ogutu, '
  '2021).',

 'Crabs are graded by size, weight, sex, shell hardness':
  'Crabs are graded by size, weight, sex, shell hardness and condition, large hard-shell '
  'crabs being preferred for meat content and transport tolerance and berried females '
  'sometimes restricted (FAO, 2025). Where the criteria are informal or applied visually a '
  'fisher may be unable to verify why a crab was placed in a particular grade. The issue is '
  'not grading itself but whether the criteria and their price consequences are transparent.',

 'Prices vary with grade, season, demand, distance to market':
  'Prices vary with grade, season, demand, distance and whether crabs are sold alive, large '
  'live crabs fetching more in urban, hotel and export markets (FAO, 2025). Small-scale '
  'fishers may accept a buyer’s price when they lack holding facilities, need cash or depend '
  'on that buyer for transport and credit; informal agreements cut transaction costs but can '
  'make the basis of a price hard to challenge (Crona et al., 2016).',

 'Transport affects survival and quality.':
  'Transport affects survival and quality. Live crabs are vulnerable to heat, dehydration and '
  'handling stress, so traders use baskets, plastic crates or wooden boxes with damp '
  'material. Long distances, poor roads and limited live-holding facilities add to the risk; '
  'shorter journeys and better containment may cut mortality without more fishing effort.',

 'Packaging controls movement, moisture and damage in transit:':
  'Packaging controls movement, moisture and damage in transit: live crabs may be tied or '
  'separated to reduce injury and cannibalism, and containers must ventilate and protect '
  'claws and legs. Export markets require consistent packaging, labels and traceability while '
  'small-scale traders use low-cost local materials.',
}

done = set()
for p in list(d.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    for opener, new in EDITS.items():
        if opener in done or not t.startswith(opener):
            continue
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
print(f'Chapters One to Three, final pass: {len(done)} paragraphs edited')
