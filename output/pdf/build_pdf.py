# -*- coding: utf-8 -*-
"""Sample size and power: plain-language justification + methodological statement."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle, Image, KeepTogether, PageBreak)
from PIL import Image as PILImage

OUT = '/home/user/python/output/Sample_Size_and_Power_Justification.pdf'
NAVY  = colors.HexColor('#1F3864')
STEEL = colors.HexColor('#1F4D78')
GREY  = colors.HexColor('#595959')
RULE  = colors.HexColor('#BFBFBF')
BAND  = colors.HexColor('#DEEAF6')
SOFT  = colors.HexColor('#F2F6FA')

S = dict(
 title=ParagraphStyle('t', fontName='Times-Bold', fontSize=19, leading=23, textColor=NAVY,
                      alignment=TA_CENTER, spaceAfter=4),
 sub=ParagraphStyle('s', fontName='Times-Roman', fontSize=12, leading=15, textColor=STEEL,
                    alignment=TA_CENTER, spaceAfter=3),
 meta=ParagraphStyle('m', fontName='Times-Italic', fontSize=9.5, leading=12, textColor=GREY,
                     alignment=TA_CENTER, spaceAfter=16),
 h1=ParagraphStyle('h1', fontName='Times-Bold', fontSize=13.5, leading=17, textColor=NAVY,
                   spaceBefore=16, spaceAfter=7),
 h2=ParagraphStyle('h2', fontName='Times-Bold', fontSize=11.5, leading=15, textColor=STEEL,
                   spaceBefore=12, spaceAfter=5),
 body=ParagraphStyle('b', fontName='Times-Roman', fontSize=10.5, leading=15,
                     alignment=TA_JUSTIFY, spaceAfter=8),
 lead=ParagraphStyle('l', fontName='Times-Roman', fontSize=11, leading=16.5,
                     alignment=TA_JUSTIFY, spaceAfter=9),
 note=ParagraphStyle('n', fontName='Times-Italic', fontSize=9, leading=12.5, textColor=GREY,
                     alignment=TA_JUSTIFY, spaceAfter=7),
 cap=ParagraphStyle('c', fontName='Times-Bold', fontSize=9, leading=12, textColor=STEEL,
                    spaceBefore=3, spaceAfter=4),
 cell=ParagraphStyle('cl', fontName='Times-Roman', fontSize=9, leading=12),
 cellb=ParagraphStyle('cb', fontName='Times-Bold', fontSize=9, leading=12),
 cellh=ParagraphStyle('ch', fontName='Times-Bold', fontSize=9, leading=12),
 cellc=ParagraphStyle('cc', fontName='Times-Roman', fontSize=9, leading=12,
                      alignment=TA_CENTER),
 cellbc=ParagraphStyle('cbc', fontName='Times-Bold', fontSize=9, leading=12,
                       alignment=TA_CENTER),
 ref=ParagraphStyle('r', fontName='Times-Roman', fontSize=8.5, leading=11.5,
                    alignment=TA_JUSTIFY, leftIndent=12, firstLineIndent=-12, spaceAfter=4),
)

def eq(name, width_cm):
    im = PILImage.open(f'eq_{name}.png'); w, h = im.size
    img = Image(f'eq_{name}.png', width=width_cm*cm, height=width_cm*cm*h/w)
    img.hAlign = 'CENTER'
    return KeepTogether([Spacer(1, 5), img, Spacer(1, 7)])

def P(t, st='body'): return Paragraph(t, S[st])

def tbl(header, rows, widths, align=None):
    ctr = {c for c, _ in (align or [])}
    data = [[Paragraph(h, S['cellh']) for h in header]]
    for r in rows:
        row = []
        for i, c in enumerate(r):
            if i in ctr:      st = 'cellbc' if i == 0 else 'cellc'
            else:             st = 'cellb'  if i == 0 else 'cell'
            row.append(Paragraph(c, S[st]))
        data.append(row)
    t = Table(data, colWidths=[w*cm for w in widths], repeatRows=1, hAlign='LEFT')
    style = [('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
             ('GRID', (0,0), (-1,-1), 0.5, colors.black),
             ('LINEBELOW', (0,0), (-1,0), 1.0, colors.black),
             ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
             ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5)]
    t.setStyle(TableStyle(style))
    return KeepTogether([Spacer(1,3), t, Spacer(1,9)])

def hrule():
    t = Table([['']], colWidths=[16.4*cm], rowHeights=[1])
    t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.7, NAVY)]))
    return KeepTogether([Spacer(1,2), t, Spacer(1,8)])

F = []
F += [P('SAMPLE SIZE AND STATISTICAL POWER', 'title'),
      P('Justification for a sample of 300 traders', 'sub'),
      P('Developing Gender-Responsive Childcare Services in Uasin Gishu County Markets &nbsp;·&nbsp; '
        'Discrete choice experiment', 'meta')]

# ---------------------------------------------------------------- PART 1
F += [P('Part 1 — Justification in plain language', 'h1'), hrule()]
F += [P('This section states the case for a sample of 300 in non-technical terms, for readers '
        'who need the reasoning rather than the derivation. Part 2 sets out the formal '
        'calculation.', 'note')]

F += [P('We propose interviewing <b>300 traders</b>. Each trader is shown six cards and asked '
        'to choose between two childcare services, so 300 traders give us 1,800 separate '
        'decisions to learn from — enough to work out what traders genuinely value, without '
        'asking any one person to sit through a long interview. We did not settle on 300 by '
        'habit. We worked out, for every possible sample size, how sharp the answers would be, '
        'and 300 is the point where the study starts producing answers we can stand behind. At '
        '300 traders, if a feature genuinely pulls traders towards one option — enough to tip '
        'choices from an even 50-50 split to about 56 out of 100 — we have roughly an '
        '<b>86% chance of detecting it</b>, rising to <b>95%</b> for a slightly stronger '
        'preference. Below about 170 traders those chances drop away quickly, and we would risk '
        'telling the County that traders showed no clear preference when the truth is simply '
        'that the sample was too small to see one. The numbers above 170 buy two further things '
        'worth paying for: ordinary findings, such as the share of traders who would actually '
        'use the service, come out accurate to within about <b>6 percentage points</b> either '
        'way; and there are enough women traders — the group this study is really about — to '
        'examine on their own rather than only as part of the whole. Allowing for traders who '
        'decline and for those who turn out not to care for young children, we would need to '
        'approach roughly <b>360</b> to finish with 300 completed interviews, which works out '
        'at about 50 per market across the six markets.', 'lead')]

F += [P('What 300 traders buys', 'h2')]
F += [P('“Power” is simply the chance that the study spots a real preference rather than '
        'missing it.', 'body')]
F += [tbl(['If a feature tips choices to…', 'Chance we detect it', 'Assessment'],
     [['54 out of 100 (very slight pull)', '44%', 'Unreliable'],
      ['55 out of 100 (slight)', '68%', 'Still risky'],
      ['<b>56 out of 100 (modest)</b>', '<b>86%</b>', '<b>Acceptable</b>'],
      ['57 out of 100 (clear)', '95%', 'Strong'],
      ['60 out of 100 (strong)', '&gt;99%', 'Virtually certain']],
     [7.4, 4.2, 4.8], align=[(1,'CENTER')])]
F += [P('The accepted standard in research is an 80% chance of detection. At 300 traders we '
        'clear that standard for any feature that tips choices to about 56 out of 100 or '
        'better, which covers the size of preference this study needs to measure.', 'body')]
F += [P('<b>One sentence for the sceptic.</b> The standard rule of thumb for experiments of '
        'this kind asks for at least 167 traders. We are proposing 300, and the extra 133 are '
        'not padding — they are what allows women traders to be analysed separately and '
        'ordinary percentages to be quoted with confidence.', 'body')]
F += [P('<b>Two things to flag honestly.</b> These figures assume the corrected choice cards '
        'are used; they do not hold for the version used in the pilot. And 300 supports '
        'studying one group in depth, not two: if the County wants men and women compared '
        'properly, that needs about 400 with a set quota, and traders with disabilities would '
        'need to be recruited deliberately rather than left to chance.', 'body')]

# ---------------------------------------------------------------- PART 2
F += [Spacer(1, 10)]
F += [P('Part 2 — Methodological statement', 'h1'), hrule()]

F += [P('2.1&nbsp;&nbsp;Primary approach: design-based calculation', 'h2')]
F += [P('For a multinomial logit model, the asymptotic variance–covariance matrix of the '
        'parameter estimates is a known function of the experimental design rather than a '
        'quantity requiring simulation (Rose &amp; Bliemer, 2013; de Bekker-Grob et al., 2015):',
        'body')]
F += [eq('omega', 10.4)]
F += [P('where <b>X</b><sub>s</sub> is the attribute matrix for choice set <i>s</i>, '
        '<b>p</b><sub>s</sub> the vector of choice probabilities and '
        '<b>P</b><sub>s</sub> = diag(<b>p</b><sub>s</sub>). Under null priors '
        '(<i>β</i> = 0) all <i>J</i> = 3 alternatives are equiprobable, so '
        '<i>p<sub>j</sub></i> = 1/3 and the information matrix is exact rather than '
        'approximated. The design comprises <i>S</i> = 18 choice sets in <i>B</i> = 3 blocks, '
        'each respondent completing <i>S/B</i> = 6 tasks. With <i>N</i> respondents allocated '
        'equally across blocks, total information scales as:', 'body')]
F += [eq('omegaN', 10.0)]
F += [P('Statistical power for H<sub>0</sub>: <i>β<sub>k</sub></i> = 0 against a two-sided '
        'alternative at significance level <i>α</i> is:', 'body')]
F += [eq('power', 12.4)]
F += [P('and the minimum detectable effect at power 1 − <i>γ</i> is:', 'body')]
F += [eq('mde', 9.4)]
F += [P('At <i>N</i> = 300 the computed standard errors range from 0.060 to 0.101 across the '
        'fourteen attribute parameters (median 0.083), with the alternative-specific constant '
        'at 0.148. This yields <b>1 − <i>γ</i> = 0.86 for <i>β</i> = 0.25</b> (odds ratio 1.28) '
        'and 0.95 for <i>β</i> = 0.30, with a minimum detectable effect of '
        '<b><i>β</i> = 0.23 at 80% power</b> and 0.27 at 90%.', 'body')]
F += [tbl(['Completed interviews', 'SE range (attributes)', 'MDE at 80% power', 'Assessment'],
     [['150', '0.085 – 0.209', '0.24 – 0.58', 'Main effects only'],
      ['200', '0.074 – 0.181', '0.21 – 0.51', 'Workable; one subgroup at a push'],
      ['<b>300</b>', '<b>0.060 – 0.148</b>', '<b>0.17 – 0.41</b>',
       '<b>Recommended</b>'],
      ['400', '0.052 – 0.128', '0.15 – 0.36', 'Precision, not new capability']],
     [3.6, 4.2, 3.6, 5.0], align=[(0,'CENTER'),(1,'CENTER'),(2,'CENTER')])]

F += [P('2.2&nbsp;&nbsp;Secondary approach: established rule of thumb', 'h2')]
F += [P('The Johnson and Orme criterion for choice experiments (Orme, 1998; Johnson &amp; '
        'Orme, 2003) requires:', 'body')]
F += [eq('jo', 8.6)]
F += [P('where <i>c</i> = 4 is the maximum number of levels on any attribute, <i>t</i> = 6 the '
        'number of tasks and <i>a</i> = 2 the number of non-status-quo alternatives.', 'body')]

F += [P('2.3&nbsp;&nbsp;Tertiary approach: G*Power cross-check', 'h2')]
F += [P('<b>G*Power implements no procedure for discrete choice experiments.</b> There is no '
        'conditional-logit option in the program, and a DCE power analysis cannot be performed '
        'in it directly. The analysis below therefore reframes the question at the level of the '
        'individual choice observation, as a one-sample test of a binomial proportion against '
        '<i>π</i><sub>0</sub> = 0.50 — the marginal representation of a single attribute '
        'contrast. This is a legitimate corroborating calculation, and is reported as such '
        'rather than as the primary method.', 'body')]
F += [P('G*Power 3.1 input parameters', 'cap')]
F += [tbl(['Field', 'Value'],
     [['Test family', 'Exact'],
      ['Statistical test', 'Proportion: difference from constant (binomial test, one sample)'],
      ['Type of power analysis', 'A priori — compute required sample size'],
      ['Tail(s)', 'Two'],
      ['Effect size g', '0.06 &nbsp;(<i>π</i><sub>1</sub> = 0.56 against <i>π</i><sub>0</sub> = 0.50)'],
      ['α err prob', '0.05'],
      ['Power (1 − β err prob)', '0.80'],
      ['Constant proportion', '0.50']],
     [5.0, 11.4])]
F += [P('Using the normal approximation underlying this test:', 'body')]
F += [eq('prop', 11.6)]
F += [P('Because the six observations contributed by each respondent are not independent, this '
        'figure must be inflated by a design effect, where <i>m</i> = 6 is the number of tasks '
        'per respondent and <i>ρ</i> the intra-respondent correlation:', 'body')]
F += [eq('deff', 10.0)]
F += [tbl(['Assumed ρ', 'Design effect D', 'Effective choice observations', 'Required N'],
     [['0.05', '1.25', '679', '114'],
      ['0.10', '1.50', '815', '136'],
      ['<b>0.15</b>', '<b>1.75</b>', '<b>951</b>', '<b>159</b>'],
      ['0.20', '2.00', '1,086', '181']],
     [3.0, 3.6, 5.6, 4.2],
     align=[(0,'CENTER'),(1,'CENTER'),(2,'CENTER'),(3,'CENTER')])]

F += [P('2.4&nbsp;&nbsp;Convergence of the three approaches', 'h2')]
F += [tbl(['Approach', 'Minimum N', 'Power at N = 300'],
     [['Design-based (Fisher information)', '≈ 170', '0.86 at β = 0.25'],
      ['Johnson &amp; Orme rule of thumb', '167', '— (not a power calculation)'],
      ['G*Power proportion test, ρ = 0.15', '159', '0.97 at <i>π</i><sub>1</sub> = 0.56']],
     [7.4, 3.4, 5.6], align=[(1,'CENTER')])]
F += [P('The three methods converge on a minimum of approximately 160 to 170 respondents; the '
        'proposed <i>N</i> = 300 exceeds all three. The G*Power route returns <i>higher</i> '
        'power at <i>N</i> = 300 than the design-based calculation, which is expected: the '
        'proportion test evaluates a single marginal contrast, whereas the design-based figure '
        'accounts for the simultaneous estimation of fifteen parameters from a specific design. '
        '<b>The design-based estimate is the conservative and methodologically appropriate one, '
        'and is the figure reported.</b>', 'body')]

F += [P('2.5&nbsp;&nbsp;Precision of descriptive estimates', 'h2')]
F += [P('For prevalence-type outcomes, applying the standard expression for a proportion with '
        '<i>p</i> = 0.5 at <i>N</i> = 300:', 'body')]
F += [eq('prec', 10.6)]
F += [P('giving a 95% confidence half-width of ±5.7 percentage points overall, and ±7.6 points '
        'within a 167-respondent subgroup.', 'body')]

F += [P('2.6&nbsp;&nbsp;Allocation and attrition', 'h2')]
F += [tbl(['Parameter', 'Value', 'Basis'],
     [['Completed interviews', '300', '50 per market across six markets'],
      ['Traders approached', '≈ 360', '≈ 15% combined refusal and screen-out'],
      ['Minimum women', '200', 'Keeps the primary population separately modellable'],
      ['Men', '100', 'Described and compared descriptively, not modelled separately'],
      ['Purposive disability sample', '40 – 60', 'Recruited through OPDs, additional to the 300'],
      ['Choice observations', '1,800', '300 respondents × 6 tasks']],
     [4.6, 2.8, 9.0], align=[(1,'CENTER')])]

F += [P('2.7&nbsp;&nbsp;Assumptions and limitations', 'h2')]
F += [P('The design-based calculation assumes null priors, which is conservative — informative '
        'priors derived from the pilot would reduce the variance estimates. It further assumes '
        'that the corrected experimental design and randomised alternative presentation are '
        'implemented; the figures do not apply to the design used in the pilot, in which '
        'position and cost were confounded across nine of twelve choice sets. Finally, '
        '<i>N</i> = 300 supports one stratified subgroup analysis but not two: separate '
        'estimation for male traders would require approximately 167 men, implying a total of '
        'roughly 400 under a sex quota, and traders with disabilities require purposive '
        'over-sampling rather than incidental capture.', 'body')]

F += [P('References', 'h2')]
for r in [
 'de Bekker-Grob, E. W., Donkers, B., Jonker, M. F., &amp; Stolk, E. A. (2015). Sample size '
 'requirements for discrete-choice experiments in healthcare: a practical guide. '
 '<i>The Patient</i>, 8(5), 373–384.',
 'Faul, F., Erdfelder, E., Lang, A.-G., &amp; Buchner, A. (2007). G*Power 3: A flexible '
 'statistical power analysis program for the social, behavioral, and biomedical sciences. '
 '<i>Behavior Research Methods</i>, 39(2), 175–191.',
 'Johnson, R., &amp; Orme, B. (2003). <i>Getting the most from CBC</i>. Sawtooth Software '
 'Research Paper Series.',
 'Orme, B. (1998). <i>Sample size issues for conjoint analysis studies</i>. Sawtooth Software '
 'Research Paper Series.',
 'Rose, J. M., &amp; Bliemer, M. C. J. (2013). Sample size requirements for stated choice '
 'experiments. <i>Transportation</i>, 40(5), 1021–1041.']:
    F += [Paragraph(r, S['ref'])]
F += [Spacer(1, 6),
      P('Bibliographic details should be verified against the journal of submission before '
        'final use. All computed figures in this document were produced in R from the study’s '
        'own experimental design; the analysis is reproducible from the files supplied with '
        'the pilot report.', 'note')]

# ---------------------------------------------------------------- build
def deco(canv, docu):
    canv.saveState()
    canv.setFont('Times-Italic', 8); canv.setFillColor(GREY)
    canv.drawString(2.2*cm, A4[1]-1.35*cm,
                    'Sample size and statistical power — Uasin Gishu childcare study')
    canv.setStrokeColor(RULE); canv.setLineWidth(0.4)
    canv.line(2.2*cm, A4[1]-1.5*cm, A4[0]-2.0*cm, A4[1]-1.5*cm)
    canv.line(2.2*cm, 1.55*cm, A4[0]-2.0*cm, 1.55*cm)
    canv.drawCentredString(A4[0]/2, 1.05*cm, f'{docu.page}')
    canv.restoreState()

docu = BaseDocTemplate(OUT, pagesize=A4, title='Sample Size and Statistical Power',
                       author='Study team', leftMargin=2.2*cm, rightMargin=2.0*cm,
                       topMargin=2.0*cm, bottomMargin=2.0*cm)
frame = Frame(docu.leftMargin, docu.bottomMargin,
              A4[0]-docu.leftMargin-docu.rightMargin,
              A4[1]-docu.topMargin-docu.bottomMargin, id='f')
docu.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=deco)])
docu.build(F)
print('saved', OUT)
