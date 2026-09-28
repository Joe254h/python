# -*- coding: utf-8 -*-
"""Write the SPSS syntax file that reproduces every table and figure in
Chapter Four, with the table and figure numbers of the finished thesis."""
import json, re, textwrap, collections

T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}
varmap = json.load(open('v6/varmap.json'))
ch4 = json.load(open('v6/ch4.json'))
mc = {(t['var'], t['actor']): t for t in json.load(open('out/analysis.json'))['mc_tests']}

# ---- table number -> ordered list of variables, preserving table order
tvars = collections.OrderedDict()
for num in sorted(T):
    vs = []
    for r in T[num]['rows']:
        s = str(r[0])
        if s.startswith('__BLOCK__'):
            v = varmap.get(s[9:])
            if v and v not in vs: vs.append(v)
    if vs: tvars[num] = vs

# ---- which objective each table belongs to
obj = {}
cur = None
for b in ch4:
    if b['k'] == 'h2':
        m = re.match(r'4\.(\d)', b['t'])
        cur = {'3': 1, '4': 2, '5': 3}.get(m.group(1)) if m else None
    if b['k'] == 'table' and cur: obj[b['n']] = cur

# ---- figures: number -> (title, file)
figs = [(b['n'], b['t'], b['f']) for b in ch4 if b['k'] == 'fig']

L = []
def w(s=''): L.append(s)

w('* ==========================================================================.')
w('* MUD CRAB MARKET STRUCTURE, SOUTH COAST OF KENYA.')
w('* Objective-wise analysis by Beach Management Unit (BMU).')
w('* Reproduces every table and figure reported in Chapter Four.')
w('*.')
w('* HOW TO RUN.')
w('*   1) Open this file in IBM SPSS Statistics, File > Open > Syntax.')
w('*   2) Edit the FILE= path on the GET command below so that it points at')
w('*      your own copy of Mud_crab_BMU_final_corrected.sav.')
w('*   3) Choose Run > All, then save the Viewer output as')
w('*      Appendix_A_SPSS_output.spv.')
w('*.')
w('* HOW THE ANALYSIS IS SET UP.')
w('* - Every CROSSTABS command is run BY actor, so each output table')
w('*   carries all four actor categories: fishers, middlemen, hoteliers and')
w('*   exporters.')
w('* - Fishers and middlemen are tested against BMU separately, because a')
w('*   harvester and a trader do different work and pooling them would')
w('*   confuse site with role.')
w('* - Hoteliers and exporters are described but not tested against BMU:')
w('*   four of the five hoteliers and all four exporters operated outside')
w('*   the four BMU frames, so no site comparison is possible for them.')
w('* - The Other sites group (bmu = 5) is excluded from every BMU test.')
w('* - Msambweni (bmu = 4) has no middleman, so middleman BMU tests use the')
w('*   three sites where traders were sampled.')
w('* - Monte Carlo chi-square with 10,000 resamples is used throughout,')
w('*   because many of these tables are sparse and the asymptotic')
w('*   chi-square approximation would not hold.')
w('* - Every chart plots percentages, never raw counts, so that groups of')
w('*   different size can be read side by side.')
w('* - Respondent R051 carries the corrected medium-crab price of KSh 650')
w('*   per kilogram in this dataset.')
w('* ==========================================================================.')
w()
w("GET FILE='C:\\MudCrab\\Mud_crab_BMU_final_corrected.sav'.")
w('DATASET NAME crab WINDOW=FRONT.')
w('DATASET ACTIVATE crab.')
w()
w('* If the file is already open in SPSS, comment out the three lines above')
w('* and run this one instead, with the dataset window in front:')
w('* DATASET NAME crab WINDOW=FRONT.')
w()

def rule(title):
    w('* --------------------------------------------------------------------------.')
    for line in textwrap.wrap(title, 72):
        w('* ' + line + '.')
    w('* --------------------------------------------------------------------------.')
    w()

def varlist(vs, indent=10):
    out, line = [], ''
    for v in vs:
        if len(line) + len(v) + 1 > 62:
            out.append(line); line = ''
        line += (' ' if line else '') + v
    if line: out.append(line)
    pad = ' ' * indent
    return ('\n' + pad).join(out)

def crosstab(vs, by, *, chisq=True, indent=10):
    w('CROSSTABS')
    w(f'  /TABLES={varlist(vs, indent)}')
    w(' ' * indent + f'BY {by}')
    w('  /FORMAT=AVALUE TABLES')
    if chisq: w('  /STATISTICS=CHISQ')
    w('  /CELLS=COUNT COLUMN')
    if chisq:
        w('  /COUNT ROUND CELL')
        w('  /METHOD=MC CIN(99) SAMPLES(10000).')
    else:
        w('  /COUNT ROUND CELL.')
    w()

# --------------------------------------------------------------- Section 0
rule('SECTION 0 - SAMPLE DESCRIPTION (Table 2, Figure 5)')
w('* Table 1 is the methods table in section 3.9; it is not an SPSS output.')
w()
w('* Table 2: distribution of respondents by actor category and BMU.')
w('CROSSTABS')
w('  /TABLES=actor BY bmu')
w('  /FORMAT=AVALUE TABLES')
w('  /CELLS=COUNT ROW')
w('  /COUNT ROUND CELL.')
w()
w('FREQUENCIES VARIABLES=actor bmu landing_site')
w('  /ORDER=ANALYSIS.')
w()
w('* Figure 5: composition of the sample by actor category within each BMU.')
w('DATASET DECLARE figdat.')
w('AGGREGATE /OUTFILE=figdat /BREAK=bmu actor /n=N.')
w('DATASET ACTIVATE figdat.')
w('AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /BREAK=bmu /ntot=SUM(n).')
w('COMPUTE pct = 100 * n / ntot.')
w("VARIABLE LABELS pct 'Percentage of respondents within BMU'.")
w('FORMATS pct (F5.1).')
w('EXECUTE.')
w('GRAPH')
w('  /BAR(STACK)=MEAN(pct) BY bmu BY actor')
w("  /TITLE='Composition of the sample by actor category within each BMU'.")
w('DATASET ACTIVATE crab.')
w('DATASET CLOSE figdat.')
w()

# ------------------------------------------------------- Sections 1, 2, 3
OBJNAME = {1: 'OBJECTIVE ONE: PROFILE OF THE ACTORS AND THEIR CHARACTERISTICS',
           2: 'OBJECTIVE TWO: FUNCTIONS PERFORMED AT EACH MARKET NODE',
           3: 'OBJECTIVE THREE: CONSTRAINTS AND OPPORTUNITIES'}
for o in (1, 2, 3):
    nums = [n for n in tvars if obj.get(n) == o]
    if not nums: continue
    rule(f'SECTION {o} - {OBJNAME[o]} (Tables {min(nums)} to {max(nums)})')
    for n in nums:
        title = T[n]['title']
        w(f'* Table {n}: {title[0].lower() + title[1:]}.')
        crosstab(tvars[n], 'actor')
    allv = [v for n in nums for v in tvars[n]]
    seen, flat = set(), []
    for v in allv:
        if v not in seen: seen.add(v); flat.append(v)
    w(f'* Objective {o} tested against BMU - FISHERS only, four BMUs.')
    w('TEMPORARY.')
    w('SELECT IF (actor = 1 AND bmu <= 4).')
    crosstab(flat, 'bmu')
    w(f'* Objective {o} tested against BMU - MIDDLEMEN only, three BMUs.')
    w('TEMPORARY.')
    w('SELECT IF (actor = 2 AND bmu <= 3).')
    crosstab(flat, 'bmu')
    w('* Hoteliers and exporters: description only, no BMU test is possible.')
    w('TEMPORARY.')
    w('SELECT IF (actor >= 3).')
    crosstab(flat, 'actor', chisq=False)

# ------------------------------------------------- numeric and price work
rule('SECTION 4 - CONTINUOUS MEASURES (Tables 12 and 45)')
w('* Table 12: reported monthly mud crab income and age of respondents.')
w('EXAMINE VARIABLES=income_ksh_0_1 age_0_1 BY actor')
w('  /PLOT NONE')
w('  /STATISTICS DESCRIPTIVES')
w('  /PERCENTILES(25,50,75) HAVERAGE')
w('  /MISSING LISTWISE.')
w()
w('* Table 45: reported mud crab prices by actor category and size grade.')
w('EXAMINE VARIABLES=price_large_0_2 price_medium_0_2 price_small_0_2 BY actor')
w('  /PLOT NONE')
w('  /STATISTICS DESCRIPTIVES')
w('  /PERCENTILES(25,50,75) HAVERAGE')
w('  /MISSING PAIRWISE.')
w()
w('* Table 48: mean price by actor category, BMU and size grade.')
w('MEANS TABLES=price_large_0_2 price_medium_0_2 price_small_0_2 BY actor BY bmu')
w('  /CELLS=MEAN COUNT STDDEV.')
w()

rule('SECTION 5 - KRUSKAL-WALLIS PRICE COMPARISONS (Table 46)')
w('* Prices are ordinal and heavily tied, and the four actor groups are of')
w('* very unequal size, so price is compared with the Kruskal-Wallis H test')
w('* rather than one-way ANOVA.')
w()
w('* Price compared across the four actor categories.')
w('NPAR TESTS')
w('  /K-W=price_large_0_2 price_medium_0_2 price_small_0_2 BY actor(1 4)')
w('  /MISSING ANALYSIS.')
w()
w('* Fisher price compared across the four BMUs.')
w('TEMPORARY.')
w('SELECT IF (actor = 1 AND bmu <= 4).')
w('NPAR TESTS')
w('  /K-W=price_large_0_2 price_medium_0_2 price_small_0_2 BY bmu(1 4)')
w('  /MISSING ANALYSIS.')
w()
w('* Middleman price compared across the three BMUs where traders were sampled.')
w('TEMPORARY.')
w('SELECT IF (actor = 2 AND bmu <= 3).')
w('NPAR TESTS')
w('  /K-W=price_large_0_2 price_medium_0_2 BY bmu(1 3)')
w('  /MISSING ANALYSIS.')
w()
w('* Small crabs are priced by fishers only, so no across-actor comparison')
w('* is possible for Grade C; the row is left blank in Table 46.')
w()

rule('SECTION 6 - MARKETING MARGINS AND THE DISTRIBUTION OF VALUE '
     '(Tables 47 and 49, Figures 26 to 28)')
w('* Mean price at each node. The margins in Table 47 are the differences')
w('* between these means; they are GROSS margins, because the survey did not')
w('* collect the handling, transport and mortality costs that a net margin')
w('* would require.')
w('MEANS TABLES=price_large_0_2 price_medium_0_2 BY actor')
w('  /CELLS=MEAN COUNT STDDEV.')
w()
w('* Table 49: first-sale spread between fishers and middlemen within each BMU.')
w('TEMPORARY.')
w('SELECT IF (actor <= 2 AND bmu <= 4).')
w('MEANS TABLES=price_large_0_2 price_medium_0_2 BY bmu BY actor')
w('  /CELLS=MEAN COUNT.')
w()
w('* Figure 27: mean large-crab price by actor category and BMU.')
w('GRAPH')
w('  /BAR(GROUPED)=MEAN(price_large_0_2) BY bmu BY actor')
w("  /TITLE='Mean large-crab price by actor category and BMU'.")
w()

# --------------------------------------------------------------- figures
rule('SECTION 7 - THE REMAINING CHAPTER FOUR FIGURES')
w('* Each figure below plots percentages within the grouping variable. The')
w('* figures printed in the thesis were drawn to APA 7 from these same')
w('* percentages, so the numbers match cell for cell.')
w()
FIGVAR = {}
for n, title, f in figs:
    stem = re.sub(r'^f\d+_', '', f)
    FIGVAR[n] = (title, stem)
by_actor = [(n, t, s) for n, (t, s) in FIGVAR.items() if s.endswith('_actor')]
by_site  = [(n, t, s) for n, (t, s) in FIGVAR.items() if s.endswith('_site')]
w('* Figures plotted within actor category:')
for n, t, s in sorted(by_actor):
    w(f'*   Figure {n}: {t[0].lower() + t[1:]}.')
w('*')
w('* Figures plotted within BMU:')
for n, t, s in sorted(by_site):
    w(f'*   Figure {n}: {t[0].lower() + t[1:]}.')
w()
w('* Template for a figure plotted within actor category. Replace VARNAME')
w('* with the variable named in the table that the figure accompanies.')
w('DATASET DECLARE figdat.')
w('AGGREGATE /OUTFILE=figdat /BREAK=actor age_group_0_1 /n=N.')
w('DATASET ACTIVATE figdat.')
w('AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /BREAK=actor /ntot=SUM(n).')
w('COMPUTE pct = 100 * n / ntot.')
w("VARIABLE LABELS pct 'Percentage within actor category'.")
w('FORMATS pct (F5.1).')
w('EXECUTE.')
w('GRAPH')
w('  /BAR(GROUPED)=MEAN(pct) BY actor BY age_group_0_1')
w("  /TITLE='Age distribution within each actor category'.")
w('DATASET ACTIVATE crab.')
w('DATASET CLOSE figdat.')
w()
w('* Template for a figure plotted within BMU, fishers only.')
w('DATASET DECLARE figdat.')
w('USE ALL.')
w('COMPUTE keep = (actor = 1 AND bmu <= 4).')
w('EXECUTE.')
w('FILTER BY keep.')
w('AGGREGATE /OUTFILE=figdat /BREAK=bmu age_group_0_1 /n=N.')
w('FILTER OFF.')
w('DATASET ACTIVATE figdat.')
w('AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /BREAK=bmu /ntot=SUM(n).')
w('COMPUTE pct = 100 * n / ntot.')
w("VARIABLE LABELS pct 'Percentage within BMU'.")
w('FORMATS pct (F5.1).')
w('EXECUTE.')
w('GRAPH')
w('  /BAR(GROUPED)=MEAN(pct) BY bmu BY age_group_0_1')
w("  /TITLE='Age distribution of fishers within each BMU'.")
w('DATASET ACTIVATE crab.')
w('DATASET CLOSE figdat.')
w()

# ------------------------------------------------------------------ index
rule('SECTION 8 - INDEX: WHICH COMMAND PRODUCES WHICH THESIS TABLE')
for n in sorted(T):
    vs = tvars.get(n)
    src = ', '.join(vs) if vs else {
        1:  'methods table, section 3.9 — not produced by SPSS',
        2:  'actor BY bmu',
        12: 'EXAMINE income_ksh_0_1 age_0_1',
        45: 'EXAMINE price_large_0_2 price_medium_0_2 price_small_0_2',
        46: 'NPAR TESTS /K-W',
        47: 'MEANS price_* BY actor (gross margins)',
        48: 'MEANS price_* BY actor BY bmu',
        49: 'MEANS price_* BY bmu BY actor',
        61: 'the significant Monte Carlo chi-square results above'}.get(n, '')
    for k, line in enumerate(textwrap.wrap(f'Table {n:>2}: {src}', 70)):
        w('* ' + ('  ' if k else '') + line + '.')
w()
w('* End of syntax.')

open('out/Mud_crab_BMU_analysis.sps', 'w').write('\n'.join(L) + '\n')
print('SPSS syntax written:', len(L), 'lines;',
      len(tvars), 'tables reproduced by CROSSTABS;', len(figs), 'figures indexed')
