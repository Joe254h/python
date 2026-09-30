# -*- coding: utf-8 -*-
"""Fix the duplicated margins section, drop stale exhibit notes, tighten the
chapter framing.

Three things are wrong in Chapter Four as it stands.

Sections 4.4.9 and 4.4.12 carry the same title, "Marketing Margins and the
Distribution of Value", and report the same chain twice. They are merged into
one section placed after the concentration results, so the chapter runs prices,
prices by site, concentration, margins, dispersion. Both tables survive,
because Table 38 decomposes the final price across nodes and Table 43 states
the same chain as margins and producer's share; only the duplicated prose goes.

Several paragraphs end in sentences that used to be notes under a figure, and
still describe bars ("A missing bar means...", "A taller bar means...") for
exhibits that are now tables. They are wrong as well as redundant.

The chapter introduction, the distribution section and the chapter summary
restate points made elsewhere and are tightened.
"""
import json, re

P = 'v6/ch4_dedup.json'
ch4 = json.load(open(P))

# ---------------------------------------------------------------- 1. stale notes
DROP = [
 'Small-grade prices were reported only by fishers. The hotelier medium-grade mean of '
 'KSh 380 is discussed below.',
 ' Shares sum to 100% within each bar.',
 ' The medium grade sold on to hoteliers is not shown, for the reason given above.',
 ' A missing bar means no respondent of that actor category was sampled at that site.',
 ' A taller bar means a narrower gap between the two nodes.',
 ' Hand collection was the dominant method at all four sites.',
 ' The 5–10 kg band was the most common at every site.',
]
notes = 0
for b in ch4:
    if b.get('k') not in ('p', 'bul', 'num'):
        continue
    for s in DROP:
        if s in b['t']:
            b['t'] = b['t'].replace(s, '').strip()
            notes += 1
print(f'stale exhibit notes removed: {notes}')

# ------------------------------------------------------- 2. rewritten paragraphs
NEW = {
 '4.1 Introduction': [
  'This chapter presents what 96 mud crab actors on the South Coast of Kenya reported about '
  'their work, following the three objectives in turn. Every table carries all four actor '
  'categories (fisher, middleman, hotelier and exporter) so the four positions in the chain '
  'can be read against one another, and each is broken down by Beach Management Unit so '
  'site differences stay visible.',

  'Four conventions govern how the tables should be read. Percentages are valid percentages '
  'within the actor category at that site, so the denominator is the number of respondents '
  'of that category who answered that item at that place, never the full 96. A hyphen means '
  'the category had no respondents at that site; a zero means they had respondents there '
  'but none gave that response. The BMU p-value appears on the first row of each actor '
  'block and is reported for fishers and middlemen only, because four of the five hoteliers '
  'and all four exporters operated outside the four BMU frames, leaving one or two '
  'respondents per cell.',

  'Categorical variables were tested against BMU using Monte Carlo chi-square with 10,000 '
  'resamples, which suits the sparse tables this sample produces. Fishers and middlemen '
  'were tested separately, because pooling a harvester with a trader would confuse site '
  'with role. Reported prices were compared with the Kruskal–Wallis test, which assumes no '
  'normality and tolerates very unequal group sizes.',
 ],

 '4.2 Distribution of Respondents': None,   # handled below, last paragraph only

 '4.6 Actor-Specific Associations With BMU': None,

 '4.7 Chapter Summary': [
  'Across the three objectives the same pattern recurs. Differences between actor '
  'categories were large and present on nearly every measure, from education and licensing '
  'through grading criteria and quality control to price and the constraint each group '
  'names. Differences between Beach Management Units were far fewer: nine significant '
  'associations from sixty-eight tests, concentrated among fishers and confined to age, '
  'marital status, training, travel time, size labelling and first buyer location, plus the '
  'single middleman constraint result.',

  'The one site difference with a direct economic consequence was in price. Fisher prices '
  'differed significantly across sites while middleman prices did not, so the gap a fisher '
  'faces at first sale is set locally: Majoreni fishers held 91.7% of the local middleman '
  'price for large crabs against close to 54% at Shimoni and Vanga. Read alongside the '
  'chain-share result, where the fisher retained between 27.5% and 39.6% of the end price, '
  'the chapter describes a market whose value is realised where the grading rule, the '
  'logistics and the connection to the final buyer sit together, and whose harvesters reach '
  'none of those things.',
 ],
}

# single-paragraph replacements, matched on their opening words
ONE = {
 'This distribution sets the limits of what the site comparisons can do.':
  'This distribution sets the limits of the site comparisons. No middleman was sampled at '
  'Msambweni, so middleman tests use the three sites where traders were interviewed. '
  'Msambweni is left out of the middleman tables rather than shown as a column of zeros: '
  'that is a gap in the realised sample, not evidence that no middlemen work there. Its '
  'three fisher respondents should be read with that in mind.',

 'Three points should be kept in mind when reading Table 53.':
  'Three points belong with Table 53. The tests carry no correction for multiple '
  'comparisons, so associations with probabilities close to .05 are exploratory rather than '
  'established, and the Monte Carlo confidence interval is given alongside each p-value so '
  'borderline cases can be judged. The nine significant results cluster in three areas: who '
  'fishes where (age, marital status, training), how far and how they describe their catch '
  '(travel time, large- and small-crab size labels, first buyer location), and what '
  'middlemen worry about (main constraint). The absence of hoteliers and exporters is a '
  'limit of the sampling frame, not a finding; neither group was sampled across enough '
  'sites for a test.',
}

cur = None; idx = 0; out = []
for b in ch4:
    if b.get('k') in ('h1', 'h2', 'h3', 'h4'):
        cur = b['t']; idx = 0
        out.append(b); continue
    if b.get('k') == 'p':
        if NEW.get(cur):
            if idx < len(NEW[cur]):
                out.append({'k': 'p', 't': NEW[cur][idx]}); idx += 1
            continue
        for opener, repl in ONE.items():
            if b['t'].startswith(opener):
                b = {'k': 'p', 't': repl}; break
    out.append(b)
ch4 = out

# ----------------------------------------------- 3. merge the two margins sections
def span(title):
    i = next(k for k, b in enumerate(ch4) if b.get('k') == 'h3' and b['t'] == title)
    j = i + 1
    while j < len(ch4) and ch4[j].get('k') not in ('h1', 'h2', 'h3'):
        j += 1
    return i, j

A = '4.4.9 Marketing Margins and the Distribution of Value'
B = '4.4.12 Marketing Margins and the Distribution of Value'
ai, aj = span(A)
t38 = next(b for b in ch4[ai:aj] if b.get('k') == 'table')
bi, bj = span(B)
t43 = next(b for b in ch4[bi:bj] if b.get('k') == 'table')

MERGED = [
 {'k': 'h3', 't': '4.4.11 Marketing Margins and the Distribution of Value'},
 {'k': 'p', 't':
  'Reading the four node prices as one chain shows where the final price accumulates. Two '
  'end points were available: large crabs leaving the middleman for an exporter finished at '
  'KSh 1,700.0 per kilogram and those going to a hotel kitchen at KSh 2,200.0. The margin '
  'at a node is what an actor adds between buying and selling, expressed against his own '
  'selling price; the producer’s share asks how much of the final price reaches the person '
  'who caught the crab.'},
 t38,
 {'k': 'p', 't':
  'As shown in Table 38, the fisher kept between a quarter and two fifths of the end price. '
  'Large crabs sold on to an exporter left 35.6% with the harvester; the same crabs sold to '
  'a hotel left 27.5%. Medium crabs going for export were the fisher’s best case at 39.6%. '
  'In every chain the largest single share was added at the last step, 44.4% between the '
  'middleman and the exporter and 57.0% between the middleman and the hotel, while the '
  'middleman, the actor most often identified with the low beach price, took the smallest '
  'share of the three, between 15.5% and 20.0%.'},
 t43,
 {'k': 'p', 't':
  'Table 43 states the same chain as margins. The middleman’s gross marketing margin was '
  '36.1% of his own selling price for large crabs and 28.3% for medium, the final node took '
  '44.4% or 57.0% of his, and the total marketing margin ran from 60.4% to 72.5% of the '
  'final price. An exporter paying KSh 945.5 and selling at KSh 1,700.0 works on a spread '
  'of KSh 754.5 per kilogram, roughly one and a quarter times what the fisher received for '
  'landing the animal.'},
 {'k': 'p', 't':
  'These are gross margins. The shares rest on group means rather than on one crab followed '
  'from beach to buyer, and the survey priced no transport, holding, ice, packaging or cost '
  'of capital, so nothing here is a profit. One cost was measured and belongs in the '
  'calculation: fishers reported a mean of 0.75 kg of dead crab a day against a mean daily '
  'catch of 7.68 kg, a loss of 10.4% of what they land. Carrying that through cuts the '
  'producer’s share from 35.6% to 31.9% in the export chain and from 27.5% to 24.6% in the '
  'hotel chain. Middlemen reported a larger absolute loss, a mean of 4.33 kg a day, but the '
  'survey did not record the volume they handle, so the same rate cannot be formed for '
  'them. The direction is still hard to argue away: the value is realised two steps beyond '
  'the point the harvester can reach.'},
]

# drop section B, drop section A, splice the merged section in where B was
ch4 = ch4[:bi] + MERGED + ch4[bj:]
ai, aj = span(A)
ch4 = ch4[:ai] + ch4[aj:]

# ------------------------------------------------- 4. renumber the 4.4.x headings
RE = re.compile(r'^4\.4\.(\d+)\s+(.*)$')
k = 0
for b in ch4:
    if b.get('k') == 'h3':
        m = RE.match(b['t'])
        if m:
            k += 1
            b['t'] = f'4.4.{k} {m.group(2)}'
print(f'Objective Two subsections renumbered 4.4.1 to 4.4.{k}')

before = json.load(open(P))
bw = sum(len(b['t'].split()) for b in before if b.get('k') in ('p', 'bul', 'num'))
aw = sum(len(b['t'].split()) for b in ch4 if b.get('k') in ('p', 'bul', 'num'))
json.dump(ch4, open(P, 'w'), ensure_ascii=False, indent=1)
titles = [b['t'] for b in ch4 if b.get('k') == 'h3' and b['t'].startswith('4.4.')]
assert len(titles) == len(set(t.split(' ', 1)[1] for t in titles)), 'duplicate subsection title remains'
print(f'Chapter Four prose: {bw:,} -> {aw:,} (saved {bw - aw:,})')
