# -*- coding: utf-8 -*-
"""Insert the six tables draft 10 covers that the earlier build did not, with
findings and interpretation written in the same register."""
import json
B = json.load(open('v6/ch4_remapped.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}

def tb(n): return dict(k='table', n=n, t=T[n]['title'])
def P(t): return dict(k='p', t=t)

# ---- block A: Tables 22-25, after Table 21 (market channel / consumer contact)
A = [
 tb(22),
 P('Table 22 records how many buyers each actor dealt with and the condition in which crabs '
   'changed hands. Among fishers, 50 (76.9%) reported a single buyer and 15 (23.1%) reported two, '
   'with the single-buyer share ranging from 16 (64.0%) at Shimoni to all three (100.0%) at '
   'Msambweni; the number of buyers was not associated with BMU (p = .412). The item was not put '
   'to the other three categories. All 65 fishers sold crabs live, and every respondent in all '
   'four actor categories — 96 of 96 — said their main buyer was a regular one.'),
 P('Those three rows together describe a market with almost no spot trading at the harvesting '
   'node. Three quarters of fishers dealt with one buyer, that buyer was a regular, and the crab '
   'was live and therefore perishable at the moment of sale. A seller in that position has little '
   'practical ability to decline the price offered, which is the condition the pricing results '
   'later in this chapter describe.'),
 tb(23),
 P('As shown in Table 23, the place of sale divided by node. Every fisher sold at the landing '
   'beach, without exception at any site. Middlemen sold in town (11, 50.0%) or at a market '
   '(10, 45.5%), with one still selling at the beach, and the pattern did not vary by BMU '
   '(p = .928). All five hoteliers and all four exporters sold in town. On knowledge of the '
   'onward sale, every fisher, every middleman and all four exporters who answered said they did '
   'not know whom the next trader sold to; no hotelier completed the item.'),
 P('This is the informational counterpart to Table 21. Not one actor upstream of the final buyer '
   'could say where the crab went next. Combined with the absence of market research reported '
   'later in Table 43, it means no actor in this chain has sight of the price two steps ahead of '
   'their own transaction.'),
 tb(24),
 P('Table 24 reports where fishers said their first buyer was located, an item answered by 63 of '
   'the 65 fishers. The locations map closely onto the landing sites themselves: Shimoni was named '
   'by 22 (34.9%), Majoreni or Aleni by 13 (20.6%), Vanga by 11 (17.5%), Kiwegu by 6 (9.5%), and '
   'the remainder named Bodo Pwani, Gasi, Mkuyuni or Mwambao. The association with BMU was the '
   'strongest recorded anywhere in this study, χ²(21, N = 61) = 125.19, p < .001, '
   '99% CI [.000, .000].'),
 P('That result needs reading with care. A near-perfect association between where a fisher lands '
   'and where his buyer sits is close to a tautology, and it is reported here for completeness '
   'rather than as a finding about market structure. What it does establish is that first sale is '
   'a local transaction: the buyer is at or beside the landing site, not in a distant market to '
   'which the fisher could take his catch instead.'),
 tb(25),
 P('Table 25 covers the second buyer, an item answered by only 15 fishers. Of those, 8 (53.3%) '
   'named Kiwegu, 4 (26.7%) Majoreni or Aleni and 3 (20.0%) Mkuyuni. The remaining 50 fishers gave '
   'no second buyer at all, which is consistent with the single-buyer pattern in Table 22 and is '
   'reported here rather than left out, because an absent alternative buyer is itself the finding.'),
]

# ---- block B: Tables 39-40, before Table 41 (tied fishers / traders)
Bk = [
 tb(39),
 P('Table 39 records depot ties and the terms attached to tied relationships. Depot owners were '
   'tied to the business for 22 middlemen (100.0%), all five hoteliers and all four exporters, but '
   'for only 1 of the 9 fishers who answered (11.1%). Where middlemen and hoteliers had tied '
   'fishers, the arrangement was credit in every case — 21 middlemen and 5 hoteliers, 100.0% of '
   'those answering. Arrangements with tied traders were more varied: every fisher who answered '
   'named credit, while middlemen named credit (7, 63.6%) or fixed price (4, 36.4%), and hoteliers '
   'and exporters named frequency of supply.'),
 P('This is the clearest statement in the chapter of what ties an upstream actor to a downstream '
   'one. It is not a contract and not a price guarantee; it is credit. Every one of the 21 '
   'middlemen with tied fishers held them through an advance, and every fisher describing his own '
   'tie to a trader described the same instrument. Read against Table 13, where 93.8% of fishers '
   'named a middleman as their source of credit, the two tables describe a single mechanism from '
   'both ends.'),
 tb(40),
 P('As shown in Table 40, arrangements with tied depot owners were reported by 56 fishers and 21 '
   'middlemen. Fishers named frequency of supply (31, 55.4%) or credit (25, 44.6%); middlemen named '
   'supply quantity (10, 47.6%), frequency of supply and credit together (7, 33.3%) or credit '
   'alone (4, 19.0%). No hotelier or exporter completed the item.'),
 P('Taken with Table 39, the pattern is that obligations become more commercial further down the '
   'chain. A fisher is held by an advance; a middleman is held by a quantity he has undertaken to '
   'deliver. Neither is a written contract in the ordinary sense, and Table 41 shows that only one '
   'of the ten fishers who answered reported having any trading agreement at all.'),
]

def insert_after_table(blocks, num, payload):
    """Insert payload after the last paragraph that follows table `num`."""
    i = next(k for k, b in enumerate(blocks) if b['k'] == 'table' and b['n'] == num)
    j = i + 1
    while j < len(blocks) and blocks[j]['k'] in ('p', 'fig'):
        j += 1
    return blocks[:j] + payload + blocks[j:]

def insert_before_table(blocks, num, payload):
    i = next(k for k, b in enumerate(blocks) if b['k'] == 'table' and b['n'] == num)
    return blocks[:i] + payload + blocks[i:]

B = insert_after_table(B, 21, A)
B = insert_before_table(B, 41, Bk)
json.dump(B, open('v6/ch4.json', 'w'), indent=1)
seq = [b['n'] for b in B if b['k'] == 'table']
print('tables in order:', seq)
print('sequential 1-60:', seq == list(range(1, 61)))
print('blocks:', len(B), '| paragraphs:', sum(1 for b in B if b['k'] == 'p'),
      '| figures:', sum(1 for b in B if b['k'] == 'fig'))
