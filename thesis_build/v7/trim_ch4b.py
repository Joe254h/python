# -*- coding: utf-8 -*-
"""Tighten the heaviest Chapter Four subsections.

The findings paragraphs narrated each table cell by cell, including
site-by-site breakdowns the reader can see in the table beside them. They now
give the actor comparison, the site pattern where it matters, and the p-value.
Every figure, p-value and cross-reference is unchanged; only the retelling is
shorter.
"""
import json

P = 'v6/ch4_dedup.json'
ch4 = json.load(open(P))

NEW = {
 '4.3.1 Demographic and Personal Characteristics': [
  'As shown in Table 3, the largest age band was 18–35 among fishers (35, 53.8%) and '
  'hoteliers (4, 80.0%), and 36–49 among middlemen (11, 50.0%) and all four exporters. '
  'The 18–35 band led at every fisher site except Majoreni, where it tied with the '
  '50–60 band at 5 (35.7%) each. All four fishers under 18 were at Shimoni. Fisher age '
  'was associated with BMU (p = .004); middleman age was not (p = .932).',

  'Table 4 shows a value chain that was almost entirely male: all 65 fishers, all 22 '
  'middlemen, four of five hoteliers (80.0%) and all four exporters. The one woman was the '
  'hotelier recorded at Shimoni. Gender varied too little among fishers and middlemen to '
  'support a test.',

  'Figure 5 shows primary education as the commonest level among fishers (44, 67.7%) and '
  'middlemen (16, 72.7%), while hoteliers held certificates (2, 40.0%) or diplomas (3, '
  '60.0%) and exporters diplomas (3, 75.0%) or a degree (1, 25.0%). No fisher or middleman '
  'reported schooling beyond secondary level and 17 fishers (26.2%) reported none at all. '
  'Education was not associated with BMU for fishers (p = .334) or middlemen (p = .928).',

  'Table 5 reports ethnic group. The Digo were the largest group among fishers (36, 55.4%) '
  'and middlemen (15, 68.2%), followed by the Duruma and the Vumba, and hoteliers split '
  'between Digo (2, 40.0%), Vumba (2, 40.0%) and Duruma (1, 20.0%). Exporters drew on '
  'groups absent upstream: Chinese (2, 50.0%), Kikuyu (1, 25.0%) and Swahili (1, 25.0%). '
  'Ethnicity was not associated with BMU for fishers (p = .368) or middlemen (p = .508).',

  'Table 6 shows most fishers (41, 63.1%) and almost all middlemen (20, 90.9%) married, as '
  'were all four exporters; hoteliers split two single (40.0%) to three married (60.0%). '
  'Marital status was associated with BMU among fishers at the margin (p = .049) but not '
  'among middlemen (p = .665).',

  'Table 7 gives experience, which spread evenly across the '
  'fisher bands, 5–10 years (22, 33.8%), 11–20 years (22, 33.8%) and over 20 years '
  '(20, 30.8%), while 16 of 22 middlemen (72.7%) had more than twenty years. Hoteliers were '
  'newest, four of five (80.0%) under five years. Experience was not associated with BMU '
  'for fishers (p = .204) or middlemen (p = .747).',

  'Read together, Tables 3 to 7 and Figure 5 show fishers and middlemen as demographically '
  'similar in some respects and distinct in others. Both were almost entirely male, '
  'primarily educated and drawn mainly from the Digo, Duruma and Vumba, and neither '
  'education nor ethnicity was associated with BMU. They diverged on age and experience: '
  'fishers concentrated in the 18–35 band, with age the only demographic characteristic '
  'significantly associated with BMU, while middlemen were older and markedly more '
  'experienced. Hoteliers and exporters held higher qualifications throughout, and '
  'exporters drew on ethnic groups absent upstream. The profile of a mud crab actor '
  'therefore follows position in the chain far more than landing site.',
 ],

 '4.3.2 Business and Operational Characteristics': [
  'Table 8 shows primary role coinciding exactly with actor category, fishers recorded as '
  'crabbers, middlemen as marketers, hoteliers as processors and exporters as exporters, '
  'each at 100.0%. Every respondent in all four categories owned or managed the operation '
  'described. Neither item varied enough within fishers or middlemen to support a test.',

  'Table 9 shows fisher operations almost entirely small-scale (64, 98.5%), with one '
  'medium-scale exception at Vanga. Middleman scale was mixed, 10 small-scale (45.5%), 10 '
  'medium-scale (45.5%) and 2 large-scale (9.1%), and the medium-scale share rose from 2 '
  '(18.2%) at Shimoni to 5 (71.4%) at Majoreni and 3 (75.0%) at Vanga. That association '
  'approached but did not reach significance (p = .050) and is treated here as '
  'provisional. All five hoteliers operated at medium scale and all four exporters at '
  'large scale. Fisher scale was not associated with BMU (p = .606).',

  'Figure 6 gives the monthly income band. Most fishers fell below KSh 13,900 (52, 80.0%), '
  'every middleman fell in the next band up, KSh 13,900–69,500, four of five hoteliers '
  '(80.0%) in that same band and one (20.0%) in the highest, and all three exporters who '
  'answered in the highest, KSh 69,501–139,000. Fisher income band came close to '
  'significance against BMU but did not reach it (p = .057).',

  'Table 10 gives the underlying '
  'figures: fishers averaged KSh 8,969.2 a month with a median of KSh 6,000.0, middlemen '
  'KSh 27,954.5, hoteliers KSh 43,000.0 and the three exporters who answered KSh 90,000.0. '
  'An exporter therefore reported roughly ten times a fisher’s monthly mud crab income. '
  'Mean age rose from 36 years among fishers to 44 among middlemen and exporters, with '
  'hoteliers at 33.',

  'Table 11 covers three indicators of business formality and Figure 7 sets licensing, '
  'credit, training and collective membership side by side. Only 13 fishers (20.0%) '
  'reported another income activity, against every middleman, hotelier and exporter. '
  'Operating licences were held by 8 of 64 fishers (12.5%) and 6 of 22 middlemen (27.3%) '
  'against every hotelier and exporter. No fisher used a business loan, whereas 16 '
  'middlemen (72.7%) did, rising to all four (100.0%) at Vanga, and two of four exporters '
  '(50.0%). None of the three items was significantly associated with BMU.',

  'Table 12 shows where credit came from. Fishers who borrowed relied overwhelmingly on '
  'middlemen (61, 93.8%), with 4 (6.2%) naming middlemen and relatives together. Middlemen '
  'relied more on exporters (12, 54.5%) than on other middlemen (10, 45.5%), and all four '
  'exporters on formal institutions. No hotelier reported a credit source. Credit source '
  'was not significantly associated with BMU for fishers (p = .124) or middlemen (p = .099).',

  'Considered together, Tables 8 to 12 and Figure 6 describe a business structure that '
  'scales and formalises down the chain. Scale rose from fishers, almost uniformly '
  'small-scale, through middlemen, whose scale varied by site and approached significance, '
  'to hoteliers at medium scale and exporters at large. Income followed the same gradient '
  'and licensing was rare upstream but universal downstream. Credit traced the line in '
  'reverse: fishers borrowed from middlemen, middlemen from exporters, exporters from '
  'banks, a single chain of dependency running from the landing beach to the export '
  'market. The actor categories are successive positions of unequal formality and unequal '
  'access to finance, not simply different occupations.',
 ],
}

# one new paragraph for each old one, in the same slot, so every table and
# figure keeps the paragraph that names it
final, cur, idx, dropped = [], None, 0, {}
for b in ch4:
    if b['k'] in ('h2', 'h3'):
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
for k in NEW:
    if dropped.get(k, 0) != len(NEW[k]):
        print(f'  WARNING {k[:40]}: {dropped.get(k)} old vs {len(NEW[k])} new')

before = sum(len(b['t'].split()) for b in ch4 if b['k'] in ('p', 'bul', 'num'))
after = sum(len(b['t'].split()) for b in final if b['k'] in ('p', 'bul', 'num'))
json.dump(final, open(P, 'w'), ensure_ascii=False, indent=1)
for k, v in dropped.items():
    print(f'  {k[:50]:52s} {v} paragraphs -> {len(NEW[k])}')
print(f'\nChapter Four prose: {before:,} -> {after:,} (saved {before - after:,})')
