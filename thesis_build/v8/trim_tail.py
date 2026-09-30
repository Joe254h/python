# -*- coding: utf-8 -*-
"""The last eighty words, taken from the four longest recommendations."""
import json
P = 'v5/ch56.json'
ch56 = json.load(open(P))
REPL = {
 'All 65 fishers graded on weight alone while 95.5% of middlemen':
  'All 65 fishers graded on weight alone while 95.5% of middlemen and every hotelier and '
  'exporter used four criteria. BMUs, fisheries officers and buyers should agree a single '
  'grading sheet for Grades A, B and C, giving weight ranges and visible quality criteria, '
  'displayed at the point of sale beside the price offered for each grade.',
 'The fisher retained 27.5% to 39.6% of the end-of-chain price':
  'The fisher retained 27.5% to 39.6% of the end-of-chain price while 44.4% to 57.0% was '
  'added at the final buyer. BMUs and the county should test one direct-supply arrangement '
  'between an organised fisher group and a hotel or exporter, with agreed grades, volumes and '
  'payment terms.',
 'Poor roads were named by 98.5% of fishers':
  'Poor roads were named by 98.5% of fishers and the lack of aggregation facilities by 90.9% '
  'of middlemen. The county should prepare one infrastructure plan naming the actor each '
  'investment serves: access routes for fishers, holding facilities for middlemen, demand '
  'coordination for hotels, freight planning for exporters.',
 'Every fisher described the price as fixed by the buyer':
  'Every fisher described the price as fixed by the buyer and fisher large-crab prices ran '
  'from KSh 535.7 at Vanga to KSh 785.7 at Majoreni. Each BMU should keep a weekly price '
  'register by grade, buyer and site, publishing the median and the observed range rather '
  'than a guaranteed price.',
 'Price fluctuation was the main constraint for 90.8% of fishers':
  'Price fluctuation was the main constraint for 90.8% of fishers while 95.5% of middlemen '
  'named price stability as their priority. County and national agencies should work on '
  'stability through reliable information, consistent grading, predictable payment terms and '
  'buyer competition rather than a guaranteed price.',
}
before = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p','bul','num'))
hit=set()
for b in ch56:
    if b.get('k') not in ('num','bul','p'): continue
    for o,n in REPL.items():
        if o in hit or not b['t'].startswith(o): continue
        b['t']=n; hit.add(o); break
missing=[o[:56] for o in REPL if o not in hit]
if missing:
    print('NOT FOUND, nothing saved:'); [print('   ',m) for m in missing]; raise SystemExit(1)
after = sum(len(b['t'].split()) for b in ch56 if b.get('k') in ('p','bul','num'))
json.dump(ch56, open(P,'w'), ensure_ascii=False, indent=1)
print(f'rewritten {len(hit)}  saved {before-after}')
