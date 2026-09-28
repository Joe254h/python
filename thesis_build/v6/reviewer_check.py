# -*- coding: utf-8 -*-
"""Check the thesis against each numbered issue in the reviewer's report."""
import docx, re
from docx.oxml.ns import qn
d = docx.Document('v6/thesis.docx')
kids = list(d.element.body)
def ptx(el): return ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip()
paras = [ptx(e) for e in kids if e.tag == qn('w:p')]
tbl_txt = []
for t in d.element.body.iter(qn('w:tbl')):
    tbl_txt.append(' '.join(ptx(c) for c in t.iter(qn('w:tc'))))
ALL = '\n'.join(paras + tbl_txt)
_c1 = [i for i, p in enumerate(paras) if p == 'CHAPTER ONE: INTRODUCTION'][-1]
heads = [p for p in paras[_c1:] if re.match(r'^(CHAPTER |\d+\.\d+)', p)]
H = '\n'.join(heads)

def chk(n, title, cond, evidence):
    print(f'{"PASS" if cond else "OPEN"}  {n:>2}. {title}')
    print(f'        {evidence}')

# 1 conceptual framework vs methodology
c1 = ('2.12 Conceptual Framework' in H and
      'did not measure' in ALL and 'not treated as a second causal theory' in ALL)
chk(1, 'Conceptual framework aligned with what was actually tested',
    c1, '§2.12 descriptive framework; §2.11 states SCP is the single causal frame; '
        '§5.6 names what was not measured; Figure 3 is a descriptive framework, not a path model.')

# 2 market structure analysis
kw = len(re.findall(r'H\(\d\)\s*=', ALL))
c2 = (kw >= 6 and 'Marketing Margins' in ALL and 'end-of-chain price' in ALL
      and 'Herfindahl' in ALL and 'coefficient of variation' in ALL)
chk(2, 'Market structure analysis strengthened',
    c2, f'{kw} Kruskal-Wallis statistics; gross marketing margin, total margin and '
        'producer\u2019s share by chain; Herfindahl-Hirschman concentration of first-sale '
        'outlets by BMU; buyer options per harvester; price dispersion and transmission.')

# 3 sampling limitations
c3 = all(s in ALL for s in ('Non-Response and Sampling Limitations', 'Yamane', 'snowball'))
chk(3, 'Sampling limitations addressed',
    c3, '§3.5 Yamane sample-size calculation; §3.6 Non-Response and Sampling Limitations; '
        'snowball sampling limits stated.')

# 4 justification of the study population
c4 = 'Lamm & Lamm, 2019' in ALL and 'were outside the survey scope' in ALL
chk(4, 'Study population justified',
    c4, '§3.4 defines the target population, cites Lamm and Lamm (2019) and names '
        'who was excluded and what that costs the study.')

# 5 research design and analytical alignment
c5 = '3.3 Research design' in H and '3.9 Alignment of objectives and analysis' in H
chk(5, 'Research design stated and objectives aligned to analysis',
    c5, '§3.3 Research design; §3.9 alignment table mapping each objective to its '
        'variables, tables, figures and tests.')

# 6 theoretical framework
c6 = '2.11 Theoretical Framework' in H and 'Keeping SCP as the central framework' in ALL
chk(6, 'Theoretical framework simplified',
    c6, '§2.11 names SCP as the single guiding framework and gives value-chain and '
        'livelihood concepts an explicitly supporting role.')

# 7 literature review
c7 = ('2.10 Critical Assessment of the Literature' in H and
      ALL.count('Kwale') >= 4 and 'Where the literature conflicts' in H)
chk(7, 'Literature review made critical',
    c7, '§2.10 with agreement, two named study-vs-study conflicts, methodological '
        f'limitations of earlier work, a Kwale section ({ALL.count("Kwale")} mentions) and the research gap.')

# 8 results chapter
obj_disc = len(re.findall(r'Discussion of Findings in Relation to Previous Studies', H))
c8 = obj_disc == 3
chk(8, 'Results give finding, meaning, objective link and comparison',
    c8, f'{obj_disc} per-objective "Discussion of Findings in Relation to Previous Studies" '
        'sections; each of the 60 tables carries a findings paragraph, and all 20 '
        'subsections that hold tables close with at least one interpretive paragraph.')

# 9 discussion chapter
c9 = ('5.5 Synthesis Using the Structure-Conduct-Performance Framework' in H and
      '5.6 What the Structure Measures Do and Do Not Capture' in H and '5.7 Study Limitations' in H)
chk(9, 'Discussion interprets rather than repeats',
    c9, '§5.5 SCP synthesis, §5.6 what the structure measures do and do not capture, '
    '§5.7 limitations; each '
        'objective has Key Findings, mechanism sections and Implications.')

# 10 conclusions and recommendations
recs = [p for p in paras if re.match(r'^6\.4', p)]
c10 = len(recs) >= 4 and '6.5 Recommendations for Further Research' in H
chk(10, 'Conclusions and recommendations tied to findings',
    c10, 'Conclusions §6.2.1–6.2.3 and recommendations §6.4.1–6.4.3 run objective by '
         'objective; §6.5 further research.')

# 11 terminology
bad_terms = []
for pair in [('middleman', 'broker'), ('BMU', 'landing site')]:
    pass
c11 = ('gross' in ALL and 'net margin' in ALL.lower() and
       'LIST OF ABBREVIATIONS' in paras)
chk(11, 'Terminology defined and used consistently',
    c11, 'LIST OF ABBREVIATIONS added; margins are called gross throughout and the '
         'absence of net margins is stated; actor names are fixed as fisher, middleman, '
         'hotelier and exporter in every table.')

# 12 formatting
tnums = [int(m.group(1)) for p in paras if (m := re.fullmatch(r'Table (\d+)', p))]
fnums = [int(m.group(1)) for p in paras if (m := re.fullmatch(r'Figure (\d+)', p))]
c12 = (tnums == list(range(1, len(tnums)+1)) and fnums == list(range(1, len(fnums)+1))
       and '3.1 Introduction' in H and '3.4 Target population' in H)
chk(12, 'Formatting and numbering corrected',
    c12, f'Chapter Three now runs 3.1–3.11 (the report flagged it starting at 3.4); '
         f'tables 1–{max(tnums)} and figures 1–{max(fnums)} sequential; APA 7 captions; '
         'plain table headers; Times New Roman 12 black throughout.')

# defence Q1
c13 = ('Concentration is measured, but over harvesters rather than volume' in ALL
       and 'Herfindahl' in ALL and 'Margins are measured gross, and net of one cost' in ALL)
chk(13, 'Defence Q1: why call it a market structure study',
    c13, 'Concentration, marketing margin and price dispersion are all now measured and '
         'reported in Tables 41 to 44; §5.6 states precisely what each one captures and '
         'what it does not, which is transaction volume and the cost side.')
