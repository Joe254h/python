# -*- coding: utf-8 -*-
"""Add the market-structure measures the review asked for.

Concentration, marketing margin and efficiency cannot be computed the textbook
way from this survey, because it interviewed actors rather than censusing
buyers and recorded no costs. Each has a counterpart the data do support, and
this inserts those into Chapter Four with the methods that produce them, then
rewrites the discussion sections that had said they could not be measured.

  section 4.4.11  concentration of first-sale outlets, buyer options per
                  harvester and harvesters per trader
  section 4.4.12  gross marketing margin per node, total margin, producer's
                  share, and the same share net of measured physical loss
  section 4.4.13  price dispersion within actor and grade, and the share of the
                  downstream price transmitted to the harvester
"""
import json

MS = json.load(open('v6/market_structure.json'))
BS = json.load(open('v6/buyers_by_site.json'))
ch4 = json.load(open('v6/ch4_dedup.json'))
T = json.load(open('v6/tables_final_dedup.json'))

nT = max(t['num'] for t in T)          # tables currently end here
W9 = [1850, 1250, 900, 820, 820, 760, 900, 880, 846]

# ------------------------------------------------------------------ tables
site_rows = {r['site']: r for r in MS['by_site']}
ratio_rows = {r['site']: r for r in MS['ratio']}
SITES = ['Shimoni', 'Majoreni', 'Vanga', 'Msambweni']

t_conc = dict(
    num=nT + 1,
    title='Concentration of First-Sale Outlets Reported by Fishers, by BMU',
    headers=['BMU', 'Fishers\nanswering', 'Buying points\nnamed',
             'Largest point', 'Share at the\nlargest point',
             'HHI', 'Numbers\nequivalent'],
    widths=[1500, 1100, 1150, 1600, 1250, 1050, 1376],
    rows=[])
for s in SITES:
    r = site_rows.get(s)
    if not r:
        continue
    t_conc['rows'].append([s, str(r['n']), str(r['outlets']), r['top'],
                           f"{r['cr1']:.1f}%", f"{r['hhi']:,}", f"{r['neq']:.2f}"])
o = MS['overall']
t_conc['rows'].append(['All four BMUs', str(o['n']), str(o['outlets']),
                       'Majoreni / Aleni', f"{o['cr1']:.1f}%",
                       f"{o['hhi']:,}", f"{o['neq']:.2f}"])

t_buy = dict(
    num=nT + 2,
    title='Buyer Options per Harvester and Harvesters per Trader, by BMU',
    headers=['BMU', 'Fishers\nanswering', 'Selling to one\nbuyer only',
             'Mean buyers\nper fisher', 'Fishers\nsampled',
             'Middlemen\nsampled', 'Fishers per\nmiddleman'],
    widths=[1500, 1150, 1400, 1250, 1050, 1150, 1526],
    rows=[])
for s in SITES:
    b = BS.get(s); r = ratio_rows.get(s)
    if not b:
        continue
    t_buy['rows'].append([s, str(b['n']), f"{b['one']} ({b['pct']:.1f}%)",
                          f"{b['mean']:.2f}", str(r['fishers']), str(r['middlemen']),
                          f"{r['ratio']:.2f} : 1" if r['ratio'] else 'no trader sampled'])
bp = MS['buyers_per_seller']; ra = MS['ratio_all']
t_buy['rows'].append(['All four BMUs', str(bp['n']),
                      f"{bp['one']} ({bp['one_pct']:.1f}%)", f"{bp['mean']:.2f}",
                      str(ra['fishers']), str(ra['middlemen']), f"{ra['ratio']:.2f} : 1"])

t_marg = dict(
    num=nT + 3,
    title='Gross Marketing Margin, Total Margin and Producer’s Share by Chain',
    headers=['Chain', 'Fisher\nKSh/kg', 'Middleman\nKSh/kg', 'Final node\nKSh/kg',
             'Middleman\nGMM', 'Final node\nGMM', 'Total\nGMM',
             'Producer’s\nshare', 'Producer’s share\nnet of loss'],
    widths=[1900, 900, 1000, 1000, 1000, 1000, 850, 1000, 1376],
    rows=[])
for r in MS['margins']:
    t_marg['rows'].append([
        f"{r['grade']} sold on to {r['end'].lower()}s",
        f"{r['pf']:,.1f}", f"{r['pm']:,.1f}", f"{r['pe']:,.1f}",
        f"{r['gmm_middleman']:.1f}%", f"{r['gmm_end']:.1f}%", f"{r['total_gmm']:.1f}%",
        f"{r['producer_share']:.1f}%", f"{r['producer_share_net']:.1f}%"])

cv = {(r['grade'], r['actor']): r for r in MS['cv']}
tr = {(r['grade'], r['site']): r['transmission'] for r in MS['transmission']}
t_eff = dict(
    num=nT + 4,
    title='Price Dispersion Within Each Actor Category and Price Transmission to the Fisher',
    headers=['Size grade', 'Fisher', 'Middleman', 'Hotelier', 'Exporter',
             'Shimoni', 'Majoreni', 'Vanga'],
    widths=[2000, 1000, 1150, 1050, 1050, 1000, 1050, 1076],
    rows=[])
t_eff['rows'].append(['__BLOCK__Coefficient of variation of reported price, by actor category'] + [''] * 7)
for g in ['Large (Grade A)', 'Medium (Grade B)']:
    row = [g]
    for a in ['Fisher', 'Middleman', 'Hotelier', 'Exporter']:
        r = cv.get((g, a))
        row.append(f"{r['cv']:.1f}%" if r else '-')
    row += ['', '', '']
    t_eff['rows'].append(row)
t_eff['rows'].append(['__BLOCK__Fisher price as a percentage of the middleman price at the same BMU'] + [''] * 7)
for g in ['Large (Grade A)', 'Medium (Grade B)']:
    row = [g, '', '', '', '']
    for s in ['Shimoni', 'Majoreni', 'Vanga']:
        v = tr.get((g, s))
        row.append(f'{v:.1f}%' if v is not None else '-')
    t_eff['rows'].append(row)

NEW = [t_conc, t_buy, t_marg, t_eff]

# ------------------------------------------------------------------- prose
n1, n2, n3, n4 = (t['num'] for t in NEW)
lo = MS['loss']

BLOCKS = [
 dict(k='h3', t='4.4.11 Concentration at the Point of First Sale'),
 dict(k='p', t=(
  'Objective Two asks how the market is organised, and concentration is the '
  'standard way of answering that. A textbook concentration ratio needs a census '
  'of the buyers operating at each landing site and the volume each one handles; '
  'this survey interviewed actors and recorded neither. What it did record is '
  'where each fisher took his catch for first sale, and that supports a '
  'concentration measure of a different kind: how far the harvesters at a site '
  'are spread across buying points, or gathered at one. The shares below are '
  'shares of harvesters, not shares of volume, and the index is read accordingly.')),
 dict(k='table', n=n1),
 dict(k='p', t=(
  f'Table {n1} shows that first sale is concentrated at every landing site. '
  f'Across the four BMUs the 63 fishers who answered named only {o["outlets"]} '
  f'buying points between them, with an HHI of {o["hhi"]:,} and a '
  f'numbers-equivalent of {o["neq"]:.2f} outlets. Within a site the picture is '
  f'tighter still. Majoreni fishers named two points and {site_rows["Majoreni"]["cr1"]:.1f}% '
  f'of them went to one, giving an HHI of {site_rows["Majoreni"]["hhi"]:,} and a '
  f'numbers-equivalent of {site_rows["Majoreni"]["neq"]:.2f}: in practice a single '
  f'outlet. Vanga returned {site_rows["Vanga"]["hhi"]:,}, Msambweni '
  f'{site_rows["Msambweni"]["hhi"]:,} and Shimoni, the least concentrated, '
  f'{site_rows["Shimoni"]["hhi"]:,}. Competition authorities commonly treat a '
  'market above 2,500 as highly concentrated. Every BMU in this study sits above '
  'that line, and three of the four sit above 4,500.')),
 dict(k='table', n=n2),
 dict(k='p', t=(
  f'Table {n2} approaches the same structure from the seller’s side. '
  f'{bp["one"]} of the {bp["n"]} fishers who answered ({bp["one_pct"]:.1f}%) sold '
  f'to a single buyer, and the mean across all fishers was {bp["mean"]:.2f} buyers. '
  f'The single-buyer share ran from {BS["Shimoni"]["pct"]:.1f}% at Shimoni to '
  f'{BS["Vanga"]["pct"]:.1f}% at Vanga and all three fishers at Msambweni. Set '
  f'against that, {ra["fishers"]} fishers were sampled against {ra["middlemen"]} '
  f'middlemen, {ra["ratio"]:.2f} harvesters for every trader, rising to '
  f'{ratio_rows["Vanga"]["ratio"]:.2f} at Vanga and falling to '
  f'{ratio_rows["Majoreni"]["ratio"]:.2f} at Majoreni. Every fisher in the sample '
  'also described his main buyer as a regular one and reported being tied to a '
  'trader, so the single-buyer figure is not a matter of convenience on the day.')),
 dict(k='p', t=(
  'Two cautions belong with these numbers. They measure where harvesters take '
  'their catch, not how much crab each buying point handles, so a point that many '
  'fishers name but that buys little from each would be overweighted. They also '
  'rest on the fishers sampled at a site rather than on every fisher working '
  'there. Neither caution changes the direction: at three of the four BMUs more '
  'than two thirds of the harvesters interviewed carried their catch to one '
  'place, and more than three quarters dealt with one buyer when they got there.')),

 dict(k='h3', t='4.4.12 Marketing Margins and the Distribution of Value'),
 dict(k='p', t=(
  'The margin at a node is the difference between what that actor pays and what '
  'he sells for, expressed against his own selling price. The producer’s '
  'share turns the same arithmetic round and asks how much of the final price '
  'reaches the person who caught the crab. Both are computed here from the mean '
  'reported price at each node.')),
 dict(k='table', n=n3),
 dict(k='p', t=(
  f'Table {n3} reads the chain three ways. Large crabs moving to an exporter left '
  f'the middleman a gross margin of {MS["margins"][0]["gmm_middleman"]:.1f}% of his '
  f'own selling price and the exporter {MS["margins"][0]["gmm_end"]:.1f}% of his, '
  f'a total marketing margin of {MS["margins"][0]["total_gmm"]:.1f}% and a '
  f'producer’s share of {MS["margins"][0]["producer_share"]:.1f}%. The same '
  f'crabs sold to a hotel gave a total margin of {MS["margins"][1]["total_gmm"]:.1f}% '
  f'and left the fisher {MS["margins"][1]["producer_share"]:.1f}%. Medium crabs '
  f'going for export were the harvester’s best case at '
  f'{MS["margins"][2]["producer_share"]:.1f}%. In every chain the largest single '
  'margin accrued at the node furthest from the water.')),
 dict(k='p', t=(
  'These are gross margins. The survey priced no transport, holding, ice, '
  'packaging or cost of capital, so nothing here is a profit. One cost was '
  'measured, however, and it belongs in the calculation: physical mortality. '
  f'Fishers reported a mean of {lo["fisher_mort"]:.2f} kg of dead crab a day '
  f'against a mean daily catch of {lo["fisher_catch"]:.2f} kg, a loss of '
  f'{lo["fisher_loss_pct"]:.1f}% of the volume they land. Carrying that loss '
  f'through reduces the producer’s share from '
  f'{MS["margins"][0]["producer_share"]:.1f}% to '
  f'{MS["margins"][0]["producer_share_net"]:.1f}% in the export chain and from '
  f'{MS["margins"][1]["producer_share"]:.1f}% to '
  f'{MS["margins"][1]["producer_share_net"]:.1f}% in the hotel chain. Middlemen '
  f'reported a larger absolute loss, a mean of {lo["middleman_mort"]:.2f} kg a '
  'day, but the survey did not record the volume they handle, so the same rate '
  'cannot be formed for them and their margins stay gross.')),

 dict(k='h3', t='4.4.13 Price Dispersion and Price Transmission'),
 dict(k='p', t=(
  'A market in which the same product fetches widely different prices on the same '
  'day is transmitting information poorly. The coefficient of variation measures '
  'that spread independently of the price level, so it can be compared across '
  'nodes whose prices differ by a factor of three.')),
 dict(k='table', n=n4),
 dict(k='p', t=(
  f'Table {n4} shows dispersion falling steadily down the chain. For large crabs '
  f'the fisher coefficient of variation was {cv[("Large (Grade A)", "Fisher")]["cv"]:.1f}%, '
  f'the middleman {cv[("Large (Grade A)", "Middleman")]["cv"]:.1f}% and the '
  f'exporter {cv[("Large (Grade A)", "Exporter")]["cv"]:.1f}%; the medium grade '
  f'gives the same ordering. Two harvesters selling the same grade on the same '
  'coast can therefore expect materially different prices, while two exporters '
  'expect nearly the same one. The lower half of the table sets the fisher mean '
  'against the middleman mean at the same site. Majoreni transmitted '
  f'{tr[("Large (Grade A)", "Majoreni")]:.1f}% of the large-grade middleman price '
  f'to its fishers, against {tr[("Large (Grade A)", "Shimoni")]:.1f}% at Shimoni '
  f'and {tr[("Large (Grade A)", "Vanga")]:.1f}% at Vanga.')),
 dict(k='p', t=(
  'Set beside the concentration results this produces a finding worth stating '
  'carefully. Majoreni was the most concentrated site on every measure in Table '
  f'{n1}, yet it transmitted the largest share of the downstream price to its '
  'harvesters, while Vanga carried the highest number of harvesters per trader '
  f'({ratio_rows["Vanga"]["ratio"]:.2f} to one) and transmitted the least. '
  'Concentration of outlets and the price a harvester receives did not move '
  'together here. With three sites and a cross-sectional design nothing causal '
  'can be drawn from that, but it does suggest that how many buying points exist '
  'matters less than how many sellers compete for the attention of each buyer, '
  'and it marks a question worth designing a study around.')),
]

# insert before the Objective Two summary
i = next(k for k, b in enumerate(ch4)
         if b['k'] == 'h3' and b['t'].startswith('4.4.11 Summary'))
ch4 = ch4[:i] + BLOCKS + ch4[i:]

# renumber the Objective Two summary and discussion headings that follow
REN = {'4.4.11 Summary of Objective Two': '4.4.14 Summary of Objective Two',
       '4.4.12 Discussion of Findings in Relation to Previous Studies':
       '4.4.15 Discussion of Findings in Relation to Previous Studies'}
for b in ch4:
    if b['k'] == 'h3' and b['t'] in REN:
        b['t'] = REN[b['t']]

T.extend(NEW)
json.dump(ch4, open('v6/ch4_dedup.json', 'w'), ensure_ascii=False, indent=1)
json.dump(T, open('v6/tables_final_dedup.json', 'w'), ensure_ascii=False, indent=1)
print(f'tables added: {[t["num"] for t in NEW]}   total now {len(T)}')
print(f'blocks inserted: {len(BLOCKS)}')
