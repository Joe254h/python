# -*- coding: utf-8 -*-
"""Tighten the four remaining heavy subsections of Objective Two.

Same approach as v7/trim_ch4b.py: one new paragraph for each old one, in the
same slot, so every table and figure keeps the paragraph that names it. The
numbers, p-values and confidence intervals are unchanged; the repeated framing
sentences are gone.

Three stale cross-references are corrected on the way: the closing paragraph of
4.4.1 pointed at "Figures 9 and 10" when the section carries Figures 8 to 10,
4.4.4 pointed at "Tables 21 to 23 and Figures 13 and 14" instead of Tables 23
to 27 and Figure 15, and 4.4.7 pointed at "Tables 28 and 29 and Figure 17"
instead of Tables 31 to 35, a section with no figure in it.
"""
import json

P = 'v6/ch4_dedup.json'
ch4 = json.load(open(P))

NEW = {
 '4.4.1 Acquisition of Crabs and Disposal of the Catch': [
  'Table 15 divides the chain at its first joint. All 65 fishers obtained crabs by catching '
  'them and every middleman, hotelier and exporter by purchase, at every site. Figure 8 '
  'shows the source following the same division: fishers caught personally, 21 of 22 '
  'middlemen (95.5%) bought from other middlemen, all five hoteliers bought from middlemen '
  'and all four exporters from middlemen or agents. The one middleman who caught personally '
  'was at Shimoni.',

  'Figure 9 covers harvesting gear, answered by fishers and by the one middleman who also '
  'caught. Hand collection dominated (47 of 65, 72.3%), ranging from 8 (57.1%) at Majoreni '
  'to 2 (100.0%) in the Other sites group, followed by scoop nets (9, 13.8%) and hooked '
  'sticks (8, 12.3%), with a single report of sweep nets. Gear was not associated with BMU '
  '(p = .144).',

  'Figure 10 gives the daily catch. The commonest band was 5–10 kg (44 of 65 fishers, '
  '67.7%), ranging from 8 (57.1%) at Majoreni to 17 (81.0%) at Vanga; 14 fishers (21.5%) '
  'reported more than 10 kg and 6 (9.2%) reported 4–5 kg, the latter concentrated at '
  'Msambweni (1, 33.3%). Daily catch was not associated with BMU (p = .453). The item was '
  'not put to middlemen, hoteliers or exporters, whose columns are blank.',

  'Table 16 reports what fishers did with the catch. Selling the whole catch was the norm '
  '(52, 80.0%), ranging from 2 (66.7%) at Msambweni to 13 (92.9%) at Majoreni, and the '
  'remaining 13 fishers (20.0%) sold three-quarters. Travel time to market was six hours '
  'for 43 fishers (66.2%) and one hour for 22 (33.8%), and it varied significantly by site '
  '(p = .010): 21 of 25 Shimoni fishers (84.0%) and all three at Msambweni reported six '
  'hours against 5 of 14 at Majoreni (35.7%). Proportion sold was not associated with BMU '
  '(p = .452).',

  'Tables 15 and 16 and Figures 8 to 10 establish the harvesting node as a seller with no '
  'holding capacity and no alternative to immediate sale. A fisher who lands 5 to 10 kg of '
  'live crab, carries it on foot for up to six hours and disposes of the whole catch the '
  'same day cannot wait for a better offer. Majoreni fishers reached market fastest, and '
  'Majoreni also turns out to be the site where fishers received the best price.',
 ],

 '4.4.2 Buyers and Market Channels': [
  'Figure 11 shows who each actor sold to. Every fisher, at every site, sold to a '
  'first-level middleman. Middlemen sold on to company agents (9, 40.9%), second-level '
  'middlemen (7, 31.8%) or exporters (5, 22.7%), with one selling to another first-level '
  'middleman; the company-agent share ran from 3 (27.3%) at Shimoni to 3 (75.0%) at Vanga, '
  'and buyer category was not associated with BMU (p = .656). Hoteliers sold to consumers '
  'and exporters to importers, in both cases without exception.',

  'Table 17 completes the picture. Fishers and middlemen supplied local markets only, '
  'hoteliers restaurants and hotels, exporters export markets. Contact with the final '
  'consumer divided as cleanly: all 65 fishers and all 22 middlemen reached the consumer '
  'only through intermediaries, while all five hoteliers and all four exporters dealt with '
  'the end buyer directly. Neither item varied enough within fishers or middlemen to '
  'support a test against BMU.',

  'Table 17 and Figure 11 answer a central part of Objective Two. The actors who know what '
  'a crab finally sells for are the two groups furthest from the water, and the two groups '
  'who catch and aggregate it never meet the person who eats it. That informational '
  'distance underlies the price results reported later in this chapter.',

  'Table 18 records buyer numbers and the condition in which crabs changed hands. Among '
  'fishers, 50 (76.9%) reported a single buyer and 15 (23.1%) reported two, the '
  'single-buyer share ranging from 17 (68.0%) at Shimoni to all three (100.0%) at '
  'Msambweni; the number of buyers was not associated with BMU (p = .412). The item was not '
  'put to the other three categories. All 65 fishers sold crabs live, and every respondent '
  'in all four actor categories, 96 of 96, said their main buyer was a regular one.',

  'Those rows describe a market with almost no spot trading at the harvesting node. Three '
  'quarters of fishers dealt with one buyer, that buyer was a regular, and the crab was '
  'live and therefore perishable at the moment of sale. A seller in that position has '
  'little practical ability to decline the price offered.',

  'As shown in Table 19, the place of sale divided by node. Every fisher sold at the '
  'landing beach, without exception at any site. Middlemen sold in town (11, 50.0%) or at a '
  'market (10, 45.5%), with one still selling at the beach, and the pattern did not vary by '
  'BMU (p = .928). All five hoteliers and all four exporters sold in town. Every fisher, '
  'every middleman and all four exporters who answered said they did not know whom the next '
  'trader sold to; no hotelier completed the item.',

  'Not one actor upstream of the final buyer could say where the crab went next. With the '
  'absence of market research reported later in Table 35, no actor in this chain has sight '
  'of the price two steps ahead of their own transaction.',

  'Table 20 reports where fishers said their first buyer was located, answered by 63 of the '
  '65 fishers. Three places accounted for more than four-fifths of first sales: Majoreni or '
  'Aleni, named by 19 (30.2%), Mkuyuni by 17 (27.0%) and Kiwegu by 16 (25.4%). Shimoni was '
  'named by 5 (7.9%), and Gasi, Vanga, Mwambao and Bodo Pwani by four fishers between them. '
  'Each is the buying point nearest a particular landing site: 16 of 25 at Shimoni (64.0%) '
  'named Mkuyuni, 12 of 13 at Majoreni (92.3%) named Majoreni or Aleni, and 15 of 20 at '
  'Vanga (75.0%) named Kiwegu. The association with BMU was the strongest recorded anywhere '
  'in this study, χ²(21, N = 61) = 125.19, p < .001, 99% CI [.000, .000].',

  'That result needs reading with care. A near-perfect association between where a fisher '
  'lands and where his buyer sits is close to a tautology, and is reported for completeness '
  'rather than as a finding about market structure. What it does establish is that first '
  'sale is local: the buyer sits at or beside the landing site, not in a distant market the '
  'fisher could take his catch to instead.',

  'Table 21 covers the second buyer, answered by only 15 fishers. Of those, 8 (53.3%) named '
  'Mkuyuni, 4 (26.7%) Majoreni or Aleni and 3 (20.0%) Kiwegu, each group drawn almost '
  'entirely from one landing site: all eight naming Mkuyuni fished at Shimoni and all four '
  'naming Majoreni or Aleni fished at Majoreni. The remaining 50 fishers gave no second '
  'buyer at all, which fits the single-buyer pattern in Table 18 and is reported here '
  'because an absent alternative buyer is itself the finding.',
 ],

 '4.4.4 Grading and Quality Control': [
  'Table 23 records the most consequential functional difference in the chapter. All 96 '
  'respondents, at every site, said they graded mud crabs, but not by the same rule. Figure '
  '15 shows how far apart the criteria were: all 65 fishers graded on weight alone, while '
  '21 of 22 middlemen (95.5%) and every hotelier and exporter combined size, weight, shell '
  'condition and claw size. The one middleman using weight alone was at Shimoni. Criteria '
  'did not vary by site among middlemen (p = 1.000) and did not vary at all among fishers.',

  'Table 24 shows the same asymmetry in quality assurance. Fishers tied the claws (65, '
  '100.0%); middlemen (21, 95.5%) and hoteliers cited packaging standards; exporters cited '
  'inspections, certification and packaging standards. Formal quality-control measures were '
  'reported by all nine downstream actors and by none of the 87 fishers and middlemen.',

  'As shown in Table 25, 53 fishers (81.5%) used the Large label for their biggest crabs '
  'while 12 (18.5%) recorded all sizes or mixed, and 50 (76.9%) assigned Grade A against 15 '
  '(23.1%) assigning a mixed grade. Every middleman, hotelier and exporter who answered '
  'used the plain labels. The fisher pattern varied significantly by site (p = .001): at '
  'Shimoni only 14 of 25 (56.0%) used the Large label, against all 14 at Majoreni and 20 of '
  '21 (95.2%) at Vanga.',

  'Table 26 shows a narrower spread for medium crabs. Sixty-three fishers (96.9%) used the '
  'Medium label and 51 (78.5%) assigned Grade B, against 14 (21.5%) who assigned a mixed '
  'grade. Every middleman and exporter used the plain labels. The medium-size label was not '
  'associated with BMU (p = .406). Hoteliers did not complete the medium-crab items.',

  'Table 27 covers the small grade, reported by fishers only. Fifty-six fishers (86.2%) used '
  'the Small label and 59 (90.8%) assigned Grade C, while 9 (13.8%) recorded mixed size and '
  '6 (9.2%) a mixed grade. Small-size labelling varied significantly by site (p = .002), '
  'with 16 of 25 Shimoni fishers (64.0%) using the plain label against all fishers at '
  'Majoreni, Vanga and Msambweni.',

  'Tables 23 to 27 and Figure 15 identify the mechanism by which value is captured '
  'downstream. A fisher can weigh a crab as accurately as anyone; what he cannot do is '
  'price the shell condition and claw size his buyer is paying for, or verify that the '
  'grade offered is the grade the animal deserves. The site variation in labelling '
  'compounds it. The survey recorded the word used, not a measured carapace width, so this '
  'is a matter of vocabulary rather than biology. A Shimoni fisher and his buyer may not '
  'mean the same thing by the word large, and that is the condition under which a grading '
  'dispute resolves in favour of the better-informed party.',
 ],

 '4.4.7 Trading Relationships and Market Information': [
  'Table 31 records depot ties and the terms attached to them. Depot owners were tied to '
  'the business for all 22 middlemen, all five hoteliers and all four exporters, but for '
  'only 1 of the 9 fishers who answered (11.1%). Where middlemen and hoteliers had tied '
  'fishers, the arrangement was credit in every case, 21 middlemen and 5 hoteliers, 100.0% '
  'of those answering. Arrangements with tied traders varied more: every fisher who '
  'answered named credit, middlemen named credit (7, 63.6%) or fixed price (4, 36.4%), and '
  'hoteliers and exporters named frequency of supply.',

  'This is the clearest statement in the chapter of what ties an upstream actor to a '
  'downstream one. It is not a contract and not a price guarantee; it is credit. Every one '
  'of the 21 middlemen with tied fishers held them through an advance, and every fisher '
  'describing his own tie described the same instrument. Read against Table 12, where 93.8% '
  'of fishers named a middleman as their credit source, the two tables describe one '
  'mechanism from both ends.',

  'As shown in Table 32, arrangements with tied depot owners were reported by 56 fishers '
  'and 21 middlemen. Fishers named frequency of supply (31, 55.4%) or credit (25, 44.6%); '
  'middlemen named supply quantity (10, 47.6%), frequency of supply and credit together (7, '
  '33.3%) or credit alone (4, 19.0%). No hotelier or exporter completed the item.',

  'Obligations become more commercial further down the chain. A fisher is held by an '
  'advance; a middleman by a quantity he has undertaken to deliver. Neither is a written '
  'contract in the ordinary sense, and Table 33 shows that only one of the ten fishers who '
  'answered had any trading agreement at all.',

  'Table 33 shows tied relationships running downward. No fisher had a fisher tied to him, '
  'yet every fisher had a trader tied to his business; 21 of 22 middlemen (95.5%) and all '
  'five hoteliers had fishers tied to theirs, while middlemen split evenly on whether they '
  'had tied traders (11 and 11). Trading agreements, formal or informal, covered 21 '
  'middlemen (95.5%) and every hotelier and exporter, against 1 of the 10 fishers who '
  'answered the item (10.0%).',

  'As shown in Table 34, fishers saw the intermediary mainly as a negotiator (41, 63.1%) '
  'rather than a marketer (24, 36.9%); middlemen described their own role as negotiation '
  'and marketing together (14, 63.6%); hoteliers saw intermediaries as marketers and '
  'exporters as both. Terms were flexible for every fisher, middleman and hotelier, while '
  'all four exporters combined flexible terms with competitive bidding. Neither item was '
  'associated with BMU (p = .925 for fishers, p = 1.000 for middlemen).',

  'Table 35 carries no variation at all, and is the more striking for it. Not one '
  'respondent in any actor category, at any site, had adopted modern equipment or conducted '
  'market research, a figure of 0% on both items across all 96 respondents.',

  'Tables 31 to 35 close the functional account. In a chain where the buyer sets the price '
  'and controls the grading rule, no actor invests in equipment and no actor gathers '
  'independent market information. Every respondent said they kept up to date by '
  'networking, so information travels along the same commercial relationships that set the '
  'terms of trade.',
 ],
}

final, cur, idx, dropped = [], None, 0, {}
for b in ch4:
    if b['k'] in ('h1', 'h2', 'h3', 'h4'):
        cur = b['t']; idx = 0
        final.append(b)
        if cur in NEW:
            dropped[cur] = 0
        continue
    if cur in NEW and b['k'] == 'p':
        dropped[cur] += 1
        if idx < len(NEW[cur]):
            final.append({'k': 'p', 't': NEW[cur][idx]})
            idx += 1
        continue
    final.append(b)

bad = False
for k in NEW:
    if dropped.get(k, 0) != len(NEW[k]):
        print(f'  WARNING {k[:44]}: {dropped.get(k)} old vs {len(NEW[k])} new')
        bad = True
if bad:
    raise SystemExit('paragraph slots do not line up; nothing written')

before = sum(len(b['t'].split()) for b in ch4 if b['k'] in ('p', 'bul', 'num'))
after = sum(len(b['t'].split()) for b in final if b['k'] in ('p', 'bul', 'num'))
json.dump(final, open(P, 'w'), ensure_ascii=False, indent=1)
for k, v in dropped.items():
    print(f'  {k[:50]:52s} {v} paragraphs -> {len(NEW[k])}')
print(f'\nChapter Four prose: {before:,} -> {after:,} (saved {before - after:,})')
