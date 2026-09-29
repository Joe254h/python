# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image as PILImage

OUT='/home/user/python/output/Sample_Size_and_Power.docx'
EQDIR='/home/user/python/output/pdf'
DPI=400
FONT='Times New Roman'
BLACK=RGBColor(0,0,0)

doc=Document()
for s in doc.sections:
    s.top_margin=Cm(2.2); s.bottom_margin=Cm(2.2)
    s.left_margin=Cm(2.5); s.right_margin=Cm(2.5)

def style(name,size,bold=False,italic=False,before=0,after=6,keep=False):
    st=doc.styles[name]; st.font.name=FONT; st.font.size=Pt(size)
    st.font.bold=bold; st.font.italic=italic; st.font.color.rgb=BLACK
    rpr=st.element.get_or_add_rPr(); rf=rpr.find(qn('w:rFonts'))
    if rf is None: rf=OxmlElement('w:rFonts'); rpr.insert(0,rf)
    for a in ('w:asciiTheme','w:hAnsiTheme','w:eastAsiaTheme','w:cstheme'):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
    for a in ('w:ascii','w:hAnsi','w:cs','w:eastAsia'): rf.set(qn(a),FONT)
    st.paragraph_format.space_before=Pt(before); st.paragraph_format.space_after=Pt(after)
    st.paragraph_format.keep_with_next=keep
style('Normal',12,after=6)
style('Heading 1',13,bold=True,before=16,after=8,keep=True)
style('Heading 2',12,bold=True,before=12,after=6,keep=True)
style('Title',16,bold=True,after=4)

def run(p,t,size=12,bold=False,italic=False,sub=False,sup=False):
    r=p.add_run(t); r.font.name=FONT; r.font.size=Pt(size)
    r.font.bold=bold; r.font.italic=italic; r.font.color.rgb=BLACK
    if sub: r.font.subscript=True
    if sup: r.font.superscript=True
    rpr=r._element.get_or_add_rPr(); rf=rpr.find(qn('w:rFonts'))
    if rf is None: rf=OxmlElement('w:rFonts'); rpr.insert(0,rf)
    for a in ('w:ascii','w:hAnsi','w:cs','w:eastAsia'): rf.set(qn(a),FONT)
    return r

def para(text='',size=12,bold=False,italic=False,after=6,before=0,align=None,justify=True):
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(after)
    p.paragraph_format.space_before=Pt(before)
    p.alignment=align if align is not None else (WD_ALIGN_PARAGRAPH.JUSTIFY if justify else None)
    if text: run(p,text,size,bold,italic)
    return p

def rich(parts, after=6, before=0):
    """parts: list of (text, kwargs) for mixed formatting."""
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(after)
    p.paragraph_format.space_before=Pt(before); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for t,kw in parts: run(p,t,**kw)
    return p

def equation(name, after=10, before=8):
    f=f'{EQDIR}/eq12_{name}.png'; w,h=PILImage.open(f).size
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(before); p.paragraph_format.space_after=Pt(after)
    p.add_run().add_picture(f, width=Inches(w/DPI))
    return p

def h1(t): return doc.add_paragraph(t, style='Heading 1')
def h2(t): return doc.add_paragraph(t, style='Heading 2')

def cell(c,t,bold=False,size=11,align=None):
    c.text=''; p=c.paragraphs[0]
    p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(2)
    if align is not None: p.alignment=align
    if t: run(p,t,size,bold)
    tcPr=c._tc.get_or_add_tcPr(); va=OxmlElement('w:vAlign')
    va.set(qn('w:val'),'center'); tcPr.append(va)

def tbl(header, rows, widths, ctr=()):
    t=doc.add_table(rows=len(rows)+1, cols=len(header))
    t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.LEFT; t.autofit=False
    for r in t.rows:
        for i,w in enumerate(widths): r.cells[i].width=Cm(w)
    C=WD_ALIGN_PARAGRAPH.CENTER
    for i,l in enumerate(header):
        cell(t.rows[0].cells[i],l,bold=True,size=11,align=C if i in ctr else None)
    trPr=t.rows[0]._tr.get_or_add_trPr()
    e=OxmlElement('w:tblHeader'); e.set(qn('w:val'),'true'); trPr.append(e)
    for ri,row in enumerate(rows,1):
        for ci,v in enumerate(row):
            cell(t.rows[ri].cells[ci],v,bold=(ci==0),size=11,align=C if ci in ctr else None)
    doc.add_paragraph().paragraph_format.space_after=Pt(4)
    return t

I=dict(italic=True)
p=doc.add_paragraph('Sample Size and Statistical Power', style='Title')
para('Discrete choice experiment, full survey — Developing Gender-Responsive Childcare '
     'Services in Uasin Gishu County Markets', size=11, italic=True, after=14, justify=False)

# ------------------------------------------------------------------ 1
h1('1.  Recommendation')
para('The full survey should complete 300 trader interviews across the six sampled markets. '
     'Each respondent answers six choice tasks, giving 1,800 choice observations. This sample '
     'estimates the choice model with standard errors between 0.060 and 0.101 on the fourteen '
     'attribute parameters, detects utility differences of 0.23 at 80% power, and holds the '
     '95% confidence interval on descriptive proportions to ±5.7 percentage points. Three '
     'independent methods set the minimum at 159 to 170 respondents; 300 provides the margin '
     'needed to model women traders as a separate stratum.')

# ------------------------------------------------------------------ 2
h1('2.  Basis of the calculation')
para('The calculation is specific to the experimental design that will be fielded, not to a '
     'generic choice experiment. That design has the following structure:')
tbl(['Design feature','Specification'],
    [['Attributes','Seven: daily cost, location within the market, opening hours, caregiver '
      'ratio and training, food provision, management model, and disability inclusion'],
     ['Levels','4, 3, 2, 3, 2, 4 and 3 respectively'],
     ['Alternatives per task','Two unlabelled services plus an opt-out '
      '(“I would keep my current arrangement”)'],
     ['Choice sets','18, allocated to three blocks of six'],
     ['Tasks per respondent','Six (one block)'],
     ['Parameters estimated','15 — fourteen dummy-coded attribute contrasts and one '
      'alternative-specific constant for the opt-out'],
     ['Criterion','D-efficient, generated by coordinate exchange under null priors']],
    [4.4,11.6])
para('The model is a conditional (multinomial) logit. Because priors are null, the three '
     'alternatives are equiprobable and the information matrix is exact rather than '
     'approximated, so the calculation below requires no simulation.')

# ------------------------------------------------------------------ 3
h1('3.  Design-based calculation')
para('For the multinomial logit model, the asymptotic variance–covariance matrix of the '
     'parameter estimates is a function of the design (Rose and Bliemer, 2013; de Bekker-Grob '
     'et al., 2015):')
equation('omega')
rich([('where ',{}),('X',dict(bold=True)),('s',dict(sub=True)),
      (' is the attribute matrix for choice set ',{}),('s',I),(', ',{}),
      ('p',dict(bold=True)),('s',dict(sub=True)),(' the vector of choice probabilities and ',{}),
      ('P',dict(bold=True)),('s',dict(sub=True)),(' = diag(',{}),('p',dict(bold=True)),
      ('s',dict(sub=True)),('). With ',{}),('N',I),
      (' respondents allocated equally across the ',{}),('B',I),(' = 3 blocks:',{})])
equation('omegaN')
rich([('Power for the null hypothesis ',{}),('β',I),('k',dict(sub=True,italic=True)),
      (' = 0 against a two-sided alternative at significance level ',{}),('α',I),(' is:',{})])
equation('power')
para('and the minimum detectable effect is:')
equation('mde')
para('Applying this to the fielded design gives the following:')
tbl(['Completed interviews','Standard error, attribute parameters','Minimum detectable effect '
     'at 80% power','95% CI half-width, proportions'],
    [['150','0.085 – 0.209','0.24 – 0.58','±8.0 points'],
     ['200','0.074 – 0.181','0.21 – 0.51','±6.9 points'],
     ['300','0.060 – 0.148','0.17 – 0.41','±5.7 points'],
     ['400','0.052 – 0.128','0.15 – 0.36','±4.9 points']],
    [3.4,4.6,4.4,3.6], ctr=(0,1,2,3))
rich([('At ',{}),('N',I),(' = 300 the median standard error across the attribute parameters is '
      '0.083 and the opt-out constant is estimated at 0.148. Power is 0.86 for a coefficient '
      'of ',{}),('β',I),(' = 0.25, equivalent to an odds ratio of 1.28, and 0.95 for ',{}),
      ('β',I),(' = 0.30. The minimum detectable effect is ',{}),('β',I),
      (' = 0.23 at 80% power and 0.27 at 90%.',{})])
tbl(['Utility coefficient','Odds ratio','Choice share against an indifferent alternative',
     'Power at N = 300'],
    [['0.15','1.16','54 : 46','0.44'],
     ['0.20','1.22','55 : 45','0.68'],
     ['0.25','1.28','56 : 44','0.86'],
     ['0.30','1.35','57 : 43','0.95'],
     ['0.40','1.49','60 : 40','> 0.99']],
    [3.6,2.8,6.2,3.4], ctr=(0,1,2,3))

# ------------------------------------------------------------------ 4
h1('4.  Rule-of-thumb check')
para('The Johnson and Orme criterion for choice experiments (Orme, 1998; Johnson and Orme, '
     '2003) requires:')
equation('jo')
rich([('where ',{}),('c',I),(' = 4 is the largest number of levels on any attribute (cost and '
      'management model), ',{}),('t',I),(' = 6 the number of tasks and ',{}),('a',I),
      (' = 2 the number of service alternatives per task.',{})])

# ------------------------------------------------------------------ 5
h1('5.  G*Power cross-check')
para('G*Power implements no procedure for discrete choice experiments. There is no '
     'conditional-logit option in the program and the model in section 3 cannot be specified '
     'in it. The cross-check below therefore reframes the question at the level of the '
     'individual choice observation, as a one-sample test of a binomial proportion against '
     '0.50 — the marginal form of a single attribute contrast. It corroborates section 3; it '
     'does not replace it.')
tbl(['G*Power field','Entry'],
    [['Test family','Exact'],
     ['Statistical test','Proportion: difference from constant (binomial test, one sample)'],
     ['Type of power analysis','A priori — compute required sample size'],
     ['Tail(s)','Two'],
     ['Effect size g','0.06'],
     ['α err prob','0.05'],
     ['Power (1 − β err prob)','0.80'],
     ['Constant proportion','0.50']],
    [5.2,10.8])
para('Under the normal approximation this test uses:')
equation('prop')
rich([('The six observations from each respondent are not independent, so this figure is '
      'inflated by a design effect, where ',{}),('m',I),(' = 6 is the number of tasks per '
      'respondent and ',{}),('ρ',I),(' the intra-respondent correlation:',{})])
equation('deff')
tbl(['Intra-respondent correlation ρ','Design effect D','Effective choice observations',
     'Respondents required'],
    [['0.05','1.25','679','114'],
     ['0.10','1.50','815','136'],
     ['0.15','1.75','951','159'],
     ['0.20','2.00','1,086','181']],
    [4.4,3.4,4.6,3.6], ctr=(0,1,2,3))
para('An intra-respondent correlation of 0.15 is the working assumption, giving 159 '
     'respondents.')

# ------------------------------------------------------------------ 6
h1('6.  Convergence of the three methods')
tbl(['Method','Minimum respondents','Power at N = 300'],
    [['Design-based (section 3)','≈ 170','0.86 at β = 0.25'],
     ['Johnson and Orme (section 4)','167','Not a power calculation'],
     ['G*Power cross-check (section 5)','159','0.97']],
    [6.4,4.4,5.2], ctr=(1,2))
rich([('The three converge on 159 to 170. The G*Power route returns higher power at ',{}),
      ('N',I),(' = 300 than the design-based calculation because it evaluates a single '
      'marginal contrast, whereas section 3 accounts for estimating fifteen parameters '
      'simultaneously from a specific design. The design-based figure is the conservative one '
      'and is the figure reported.',{})])

# ------------------------------------------------------------------ 7
h1('7.  Descriptive precision')
para('For prevalence outcomes such as the share of traders who would use the service:')
equation('prec')
rich([('At ',{}),('N',I),(' = 300 with ',{}),('p',I),(' = 0.5 this gives ',{}),('d',I),
      (' = ±5.7 percentage points. Within a 167-respondent stratum it widens to ±7.6 points.',{})])

# ------------------------------------------------------------------ 8
h1('8.  Sample allocation')
tbl(['Parameter','Value','Basis'],
    [['Completed interviews','300','50 per market across six markets'],
     ['Traders approached','360','Allows 15% for refusal and for screen-out at B12 and B13'],
     ['Women','200 minimum','Keeps the primary population separately modellable'],
     ['Men','100','Described and compared descriptively, not modelled separately'],
     ['Purposive disability sample','40 – 60','Recruited through organisations of persons with '
      'disabilities, additional to the 300'],
     ['Choice observations','1,800','300 respondents × 6 tasks']],
    [4.4,2.8,8.8], ctr=(1,))

# ------------------------------------------------------------------ 9
h1('9.  Assumptions and limitations')
para('Null priors. The calculation assumes no prior knowledge of the coefficients, which is '
     'conservative. Priors estimated from the pilot would reduce the variance estimates, so '
     'the figures above understate the precision the full survey will achieve.')
para('Corrected design. The figures apply to the eighteen-card design with randomised '
     'presentation order. They do not apply to the design used in the pilot, in which the '
     'cheaper alternative appeared in the first position on nine of twelve cards; price and '
     'position were confounded there to the point that the cost coefficient reversed sign when '
     'a position term was added, and no willingness-to-pay estimate could be reported.')
para('One stratum, not two. A sample of 300 supports separate estimation for women traders but '
     'not simultaneously for men. A properly powered comparison of men and women requires '
     'approximately 167 in each group, implying a total of about 400 under a sex quota.')
para('Purposive recruitment for disability. Traders with disabilities, and traders caring for '
     'children with disabilities, will not reach an analysable number through incidental '
     'capture at this sample size. If the inclusion objective is to be modelled rather than '
     'described, the purposive sample in section 8 is required.')

# ------------------------------------------------------------------ 10
h1('References')
for r in ['de Bekker-Grob, E. W., Donkers, B., Jonker, M. F. and Stolk, E. A. (2015). Sample '
          'size requirements for discrete-choice experiments in healthcare: a practical guide. '
          'The Patient, 8(5), 373–384.',
          'Faul, F., Erdfelder, E., Lang, A.-G. and Buchner, A. (2007). G*Power 3: a flexible '
          'statistical power analysis program for the social, behavioral, and biomedical '
          'sciences. Behavior Research Methods, 39(2), 175–191.',
          'Johnson, R. and Orme, B. (2003). Getting the most from CBC. Sawtooth Software '
          'Research Paper Series.',
          'Orme, B. (1998). Sample size issues for conjoint analysis studies. Sawtooth Software '
          'Research Paper Series.',
          'Rose, J. M. and Bliemer, M. C. J. (2013). Sample size requirements for stated choice '
          'experiments. Transportation, 40(5), 1021–1041.']:
    p=para(r, size=11, after=5)
    p.paragraph_format.left_indent=Cm(0.75); p.paragraph_format.first_line_indent=Cm(-0.75)

doc.save(OUT); print('saved', OUT)
