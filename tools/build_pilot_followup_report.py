# -*- coding: utf-8 -*-
"""Rebuild the trader questionnaire: user's recommendations applied, sequential
numbering, consistent fonts. Source DCE cards are copied verbatim from the input."""
import copy
import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = '/root/.claude/uploads/920ad5d8-6e07-5909-9e17-40c3ac0fe128/616f4043-Joel_Questionnaire_Objective_Aligned_Reviewed_final.docx'
OUT = '/home/user/python/output/Pilot_Followup_DCE_and_Full_Study_Design.docx'

BODY_FONT = 'Calibri'
NAVY   = RGBColor(0x1F, 0x38, 0x64)
STEEL  = RGBColor(0x1F, 0x4D, 0x78)
GREY   = RGBColor(0x59, 0x59, 0x59)
RED    = RGBColor(0xC0, 0x00, 0x00)
BLACK  = RGBColor(0x00, 0x00, 0x00)

src = Document(SRC)
doc = Document()

# ---------------------------------------------------------------- page setup
for s in doc.sections:
    s.top_margin = Cm(2.0); s.bottom_margin = Cm(2.0)
    s.left_margin = Cm(2.0); s.right_margin = Cm(1.8)

def style(name, font=BODY_FONT, size=11, bold=False, italic=False,
          color=BLACK, before=0, after=4, keep=False):
    st = doc.styles[name]
    st.font.name = font; st.font.size = Pt(size)
    st.font.bold = bold; st.font.italic = italic; st.font.color.rgb = color
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)
    # drop theme references so the explicit font wins unambiguously
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rf.set(qn(a), font)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = keep
    return st

style('Normal', size=11, after=4)
style('Heading 1', size=15, bold=True, color=NAVY, before=18, after=8, keep=True)
style('Heading 2', size=12.5, bold=True, color=STEEL, before=12, after=6, keep=True)
style('Heading 3', size=11.5, bold=True, color=STEEL, before=10, after=4, keep=True)
style('Title', size=20, bold=True, color=NAVY, before=0, after=6)

def _shade(cell, hexval):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexval)
    tcPr.append(sh)

def _repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement('w:tblHeader'); el.set(qn('w:val'), 'true')
    trPr.append(el)

def _cell_text(cell, text, bold=False, size=10, align=None, color=BLACK):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    r.font.name = BODY_FONT; r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color
    return p

# ---------------------------------------------------------------- paragraph helpers
def para(text='', size=11, bold=False, italic=False, color=BLACK,
         before=0, after=4, indent=0, style_name=None):
    p = doc.add_paragraph(style=style_name)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if text:
        r = p.add_run(text)
        r.font.name = BODY_FONT; r.font.size = Pt(size)
        r.font.bold = bold; r.font.italic = italic; r.font.color.rgb = color
    return p

def h1(text):
    p = doc.add_paragraph(text, style='Heading 1')
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement('w:pBdr'); bo = OxmlElement('w:bottom')
    bo.set(qn('w:val'), 'single'); bo.set(qn('w:sz'), '6')
    bo.set(qn('w:space'), '4'); bo.set(qn('w:color'), '1F3864')
    b.append(bo); pPr.append(b)
    return p

def h2(text):
    return doc.add_paragraph(text, style='Heading 2')

def h3(text):
    return doc.add_paragraph(text, style='Heading 3')

def q(num, text, codes=None, indent_codes=True):
    """Numbered question: bold number, regular text, optional code line."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(1.05)
    p.paragraph_format.first_line_indent = Cm(-1.05)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(num + '  ')
    r.font.name = BODY_FONT; r.font.size = Pt(11); r.font.bold = True
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(11)
    if codes:
        c = doc.add_paragraph()
        c.paragraph_format.space_before = Pt(0); c.paragraph_format.space_after = Pt(3)
        c.paragraph_format.left_indent = Cm(1.05 if indent_codes else 0)
        rc = c.add_run(codes)
        rc.font.name = BODY_FONT; rc.font.size = Pt(10.5)
    return p

def instr(text):
    """Interviewer instruction — italic grey."""
    return para(text, size=10, italic=True, color=GREY, before=2, after=4, indent=1.05)

def filt(text):
    """Skip / filter logic — bold italic red so enumerators cannot miss it."""
    return para(text, size=10, bold=True, italic=True, color=RED,
                before=3, after=4, indent=1.05)

def note(text):
    """Analysis / design note for the study team."""
    p = para('', before=4, after=6)
    r = p.add_run('NOTE.  ')
    r.font.name = BODY_FONT; r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = STEEL
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(10); r2.font.italic = True; r2.font.color.rgb = GREY
    return p

def bullet(text, size=11):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(1.45)
    r = p.add_run(text)
    r.font.name = BODY_FONT; r.font.size = Pt(size)
    return p

def rule():
    para('', after=0)

def table(rows, cols, widths=None, header=True, font=10):
    t = doc.add_table(rows=rows, cols=cols)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    return t

def fill_header(t, labels, size=9.5):
    for i, lab in enumerate(labels):
        _cell_text(t.rows[0].cells[i], lab, bold=True, size=size,
                   align=WD_ALIGN_PARAGRAPH.CENTER)
        _shade(t.rows[0].cells[i], 'DEEAF6')
    _repeat_header(t.rows[0])

def page_break():
    doc.add_page_break()

# footer with page number
def add_footer():
    for s in doc.sections:
        p = s.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run('Trader Questionnaire v2.0  ·  Uasin Gishu Market Childcare Study  ·  Page ')
        r.font.name = BODY_FONT; r.font.size = Pt(8); r.font.color.rgb = GREY
        fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE')
        rr = OxmlElement('w:r'); rpr = OxmlElement('w:rPr')
        sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '16'); rpr.append(sz)
        rr.append(rpr); fld.append(rr)
        p._p.append(fld)

YN   = '1 = Yes    2 = No'
YNDK = '1 = Yes    2 = No    3 = Don’t know'
YNDR = '1 = Yes    2 = No    3 = Don’t know    4 = Refused'


def body(t, size=11, after=6): return para(t, size=size, after=after)
def kv(lbl, txt, size=10.5):
    p = para('', before=2, after=3, indent=0.5)
    r = p.add_run(lbl + '  '); r.font.name=BODY_FONT; r.font.size=Pt(size); r.font.bold=True; r.font.color.rgb=STEEL
    r2 = p.add_run(txt); r2.font.name=BODY_FONT; r2.font.size=Pt(size)
    return p
def callout(lbl, text, color=STEEL, hexc='1F4D78'):
    p = para('', before=6, after=8); p.paragraph_format.left_indent = Cm(0.5)
    pPr = p._p.get_or_add_pPr(); b = OxmlElement('w:pBdr'); e = OxmlElement('w:left')
    e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'18'); e.set(qn('w:space'),'8'); e.set(qn('w:color'),hexc)
    b.append(e); pPr.append(b)
    r = p.add_run(lbl + '  '); r.font.name=BODY_FONT; r.font.size=Pt(10.5); r.font.bold=True; r.font.color.rgb=color
    r2 = p.add_run(text); r2.font.name=BODY_FONT; r2.font.size=Pt(10.5)
    return p
def finding(text): return callout('Finding:', text)
def action(text):  return callout('What to do:', text, RED, 'C00000')
def tbl(header, rows, widths, size=9, hdrsize=9):
    t = table(len(rows)+1, len(header), widths=widths)
    fill_header(t, header, size=hdrsize)
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            _cell_text(t.rows[ri].cells[ci], val, bold=(ci==0), size=size)
    return t

p = doc.add_paragraph('PILOT FOLLOW-UP', style='Title'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para('What the choice experiment is telling us, what to change in the questionnaire, '
     'and how large the full study needs to be', size=12.5, bold=True, color=STEEL,
     after=2).alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Gender-Responsive Childcare Services in Uasin Gishu County Markets  ·  '
     'Companion to the Pilot DCE Reliability and Validity Report',
     size=10, italic=True, color=GREY, after=14).alignment = WD_ALIGN_PARAGRAPH.CENTER

h2('In one page')
body('The pilot did its job. Twenty-three traders completed all six choice tasks each — a '
     '100% task completion rate — and the fieldwork ran. What the pilot also did, which is '
     'the point of a pilot, is expose two faults that would have wasted the full survey if '
     'they had gone undetected.')
body('The first is a design fault. On nine of the twelve choice cards used, the cheaper '
     'option was printed on the left. Price and position therefore move together on 75% of '
     'cards, and no analysis can fully separate them. Adding a single term for position '
     'moves the price coefficient from −0.85 to +1.31 — from "people prefer cheaper" to '
     '"people prefer to pay more". Neither figure is trustworthy, and no willingness-to-pay '
     'number can be reported from this pilot.')
body('The second is a respondent-engagement fault. Four of the twenty-three traders chose '
     'the left-hand option on all six tasks. Remove those four and the position effect is no '
     'longer statistically significant. So this is not a general left-side bias among '
     'traders; it is a small number of people not engaging with the task, sitting on top of '
     'a design that made the left side look consistently cheaper.')
body('Both are fixable, and the fixes are different. The design is replaced with a balanced '
     'one. The engagement problem is handled by rotating which option appears first and by '
     'flagging straight-lining automatically in the form.')
finding('The pilot cannot tell us what traders value in a childcare service. It was never '
        'going to — twelve cards and fifteen parameters leaves too little information. What '
        'it can and did tell us is whether the instrument works. That question has been '
        'answered, and the answer is "after these corrections, yes".')
body('The study is achievable. We recommend 300 completed interviews for the full round, '
     'which supports the main model comfortably and allows two subgroups to be analysed '
     'separately. The reasoning is in section 5.', after=10)

page_break()
h1('1.  What the choice experiment actually shows')

h2('1.1  The headline number, and why it misleads')
tbl(['Measure', 'Result', 'What it means'],
    [['Tasks completed', '138 of 138 (23 traders x 6)',
      'No task fatigue. Six cards is a workable length.'],
     ['Chose Alternative A', '59.1%  (95% CI 50.2–67.6, p = 0.045)',
      'Looks like a left-side bias.'],
     ['Chose the cheaper option', '47.7%  (63 of 132)',
      'A coin flip. Price is not visibly driving choices.'],
     ['Opted out entirely', '4.3%',
      'Traders engaged with the service options rather than refusing them.'],
     ['Cards where A was cheaper', '9 of 12  (75%)',
      'The reason the first two rows disagree.']],
    widths=[4.0, 4.6, 7.6])
body('If traders were answering on price, the "chose cheaper" figure would be high, because '
     'the cheaper option was usually on the left. It is not high. They were not answering on '
     'price. But because the cheaper option was usually on the left, we cannot cleanly '
     'measure what they were answering on.', after=6)

h2('1.2  The cost coefficient changes sign')
tbl(['Model', 'Cost coefficient', 'Position (A)', 'Log-likelihood'],
    [['Attributes only', '−0.850  (p = 0.159)', 'not included', '−104.61'],
     ['Attributes + position', '+1.306  (p = 0.315)', '+1.581  (p = 0.048)', '−102.51']],
    widths=[4.6, 4.4, 4.2, 3.0])
body('The likelihood-ratio test for adding the position term gives chi-squared 4.20 on 1 '
     'degree of freedom, p = 0.041. So position earns its place in the model — and once it '
     'is there, price flips sign and stays insignificant.')
finding('A positive price coefficient means the model is saying traders prefer to pay more. '
        'That is not a finding about traders; it is the model telling us the data cannot '
        'separate price from position. Any willingness-to-pay figure computed from this '
        'pilot would be an artefact.')

h2('1.3  It is four people, not a general bias')
body('Four of the twenty-three traders chose Alternative A on every one of their six tasks. '
     'Dropping those four and refitting:')
tbl(['Term', 'All 23 traders', 'Excluding the 4 straight-liners'],
    [['Position (A)', '+1.581  (p = 0.048)', '+0.990  (p = 0.414)'],
     ['Cost', '+1.306  (p = 0.315)', '+0.453  (p = 0.833)'],
     ['Opt-out constant', '−2.248  (p = 0.102)', '−5.170  (p = 0.074)']],
    widths=[5.0, 5.6, 5.6])
body('The position effect is no longer significant. This matters for the fix: if traders '
     'generally favoured the left, we would need to rotate positions and little else. '
     'Because it is concentrated in four non-engaged respondents, we also need the form to '
     'detect that behaviour while the enumerator is still with the respondent.', after=6)

h2('1.4  What the pilot can and cannot support')
tbl(['Question', 'Can the pilot answer it?', 'Why'],
    [['Does the instrument work in the field?', 'Yes',
      'All tasks completed, median interview 42.5 minutes, routing behaved.'],
     ['Is the choice task understood?', 'Mostly',
      '19 of 23 traded off between options; 4 did not engage.'],
     ['What do traders value in a service?', 'No',
      'Not one attribute reaches significance. 12 cards, 15 parameters.'],
     ['What would they pay?', 'No',
      'The price coefficient is insignificant and sign-unstable.'],
     ['Which management model do they prefer?', 'No',
      'All four operator coefficients are insignificant.'],
     ['Is the design fit for the full study?', 'No — and it has been replaced',
      'The fielded design confounds price with position.']],
    widths=[5.2, 3.8, 7.2])
body('Nothing in the third to fifth rows should be read as "traders are indifferent". The '
     'pilot simply does not carry enough information to measure those things, which is the '
     'expected outcome for a sample of this size and was not its purpose.', after=10)

page_break()
h1('2.  Changes to the questionnaire, and why')
body('Each change below is tied to a specific pilot result. Nothing is changed on preference '
     'alone.')
tbl(['#', 'Change', 'Evidence from the pilot', 'What it fixes'],
    [['1', 'Rotate which option is shown first, per respondent per card, and record the '
           'order shown',
      'Cheaper option appeared on the left on 9 of 12 cards; position term significant '
      '(p = 0.048)',
      'Breaks the price–position confound structurally, so it cannot recur whatever the '
      'design'],
     ['2', 'Replace the 12-card design with the balanced 18-card design (3 blocks of 6)',
      'No attribute estimable; every standard error large',
      'Gives enough independent variation to estimate the model; all four management models '
      'appear equally in every block'],
     ['3', 'Record the block shown as a data field',
      'Block was recorded as free text ("Block 1 (Odd-numbered IDs)")',
      'With three blocks the analysis cannot proceed without a clean block variable'],
     ['4', 'Flag straight-lining automatically and prompt the enumerator',
      '4 of 23 chose the same side on all six tasks',
      'Catches non-engagement while the enumerator is still present, instead of in analysis '
      'months later'],
     ['5', 'Standardise the wording of every attribute level across cards',
      'Two levels were written two ways ("Private operator" vs "Private operator (Operator '
      'complaints)"; two wordings for no accommodation)',
      'Prevents the same level being coded as two different things'],
     ['6', 'Capture interview start and end explicitly; do not rely on form open/close',
      'Median 42.5 min, but 3 interviews recorded over 3 hours and one at 18 hours',
      'Makes duration usable as a quality measure'],
     ['7', 'Drop E1h from any composite; keep it as a standalone item',
      'Zero variance — every trader gave the same answer',
      'An item with no variation cannot belong to a scale'],
     ['8', 'Analyse E1 and E6 item by item; do not sum them',
      'E1 alpha 0.483; E6 alpha 0.600 as collected but 0.048 once the two reverse-worded '
      'items are corrected',
      'Neither is a coherent scale; summing produces a number that measures nothing'],
     ['9', 'Align the direction of the E6 statements, or mark the reversed ones in the form',
      'E6a and E6b run opposite to E6c–E6g; item-total correlations turn negative when '
      'corrected',
      'Removes the main reason the scale falls apart']],
    widths=[0.9, 4.4, 5.6, 5.3])
action('Items 1 to 4 are the ones that must be in place before the next interview. Items 5 '
       'to 9 affect analysis rather than fieldwork and can follow.')

page_break()
h1('3.  Which variables matter, on the evidence so far')
body('This ranks variables by whether the pilot showed them to be measurable, discriminating '
     'and load-bearing for the study objectives — not by how interesting they sound.')

h2('3.1  Carry these — they work and they answer the objectives')
tbl(['Variable', 'Why it earns its place'],
    [['B24 / B25 gross and net daily takings',
      'Complete, well spread, and the only affordability anchor. Everything about price rests on it.'],
     ['B27 / B27a / B27c lost trading days and income',
      'The productivity-loss estimate. It is the benefit side of the business case and cannot be recovered from any other question.'],
     ['C7 current care arrangement, C8 amount paid, C15 hours needed',
      'Current behaviour and current spending. Revealed conduct is a stronger anchor for willingness to pay than anything stated.'],
     ['E2 / E2a barriers and the single main barrier',
      'Discriminated well and maps directly onto uptake.'],
     ['E3a–E3d schedule and acceptable distance',
      'The operational specification. The service cannot be designed without it.'],
     ['E4 responsibility matrix',
      'The only demand-side evidence on governance, and it feeds the model comparison directly.'],
     ['C12 / C13 Washington Group items',
      'Standard, comparable, and the gate for the whole inclusion module.'],
     ['Section F choice tasks (rebuilt)',
      'Once the design and rotation are fixed this becomes the core of objective ii.']],
    widths=[5.2, 11.0])

h2('3.2  Keep, but treat as single items — not as scales')
tbl(['Variable', 'What the pilot showed', 'How to use it'],
    [['E1a–E1l attribute importance', 'Alpha 0.483; E1h has no variance at all; 76% of all '
      'answers sit at 3 or 4',
      'Report item by item. Do not build an importance index. The ceiling effect means it '
      'ranks poorly — the choice experiment is the better instrument for the same question.'],
     ['E6a–E6g norms', 'Alpha 0.600 as collected, 0.048 corrected; several item-total '
      'correlations negative',
      'Report item by item. E6c (men would support) and E6f (childcare is good value) behaved '
      'best and are worth keeping as individual indicators.'],
     ['B26 income variability', 'Usable but coarse',
      'Pair with B26a best/worst day figures rather than using alone.']],
    widths=[4.2, 5.6, 6.4])

h2('3.3  Fix before relying on them')
tbl(['Variable', 'Problem', 'Fix'],
    [['Interview duration', 'Form open/close is not interview length — one case at 18 hours',
      'Explicit start and end questions, or use the Kobo audit log'],
     ['F0d block', 'Stored as descriptive text tied to odd/even IDs', 'Store a clean 1/2/3 code'],
     ['DCE attribute levels', 'Two levels written two different ways across cards',
      'One canonical wording per level, applied everywhere'],
     ['E1h secure entry', 'No variance', 'Keep as a standalone descriptive; exclude from any index']],
    widths=[3.8, 6.0, 6.4])

page_break()
h1('4.  Is the study achievable?')
body('Yes, with the corrections in section 2 in place. It is worth being precise about what '
     '"achievable" means for each of the four objectives, because they are not equally well '
     'served by the instruments we have.')
tbl(['Objective', 'Achievable?', 'On what evidence'],
    [['i. Feasibility and implementation readiness', 'Yes, but not from this questionnaire',
      'It depends on the county interview, the facility assessment and provider interviews. '
      'The provider interview guide still does not exist — that is the binding gap.'],
     ['ii. Demand, preferences and willingness to pay', 'Yes, after the design is replaced',
      'The pilot showed the task is completable and understood by 19 of 23. With the balanced '
      '18-card design and rotation, the full sample will estimate it.'],
     ['iii. Inclusion barriers and design requirements', 'Yes',
      'The Washington Group items and Section H performed as intended. The main constraint is '
      'how many traders with disabilities the sample reaches — see 5.3.'],
     ['iv. Trade-offs between the four models', 'Partly',
      'The demand side will be there. The cost side depends on the costing template being '
      'filled with real provider figures. Without that, models can be ranked on preference '
      'but not on affordability.']],
    widths=[4.4, 3.6, 8.2])
finding('The honest overall position: the demand side of this study is in good shape once the '
        'design is fixed. The supply side is not yet, because two instruments — the provider '
        'interview guide and the completed costing template — do not exist. Objective iv '
        'cannot be answered without them, and no increase in trader sample size compensates.')

h1('5.  How many traders to interview')

h2('5.1  What the design itself implies')
body('Rather than rely on a rule of thumb, the precision was computed directly from the '
     'replacement design. With N traders split evenly across the three blocks, the '
     'information available is (N / 3) times the information in the full 18-card design. '
     'That gives the standard error of every parameter at any N.')
tbl(['Completed interviews', 'Typical standard error', 'Smallest effect detectable (80% power)',
     'Verdict'],
    [['150', '0.09 – 0.21', '0.24 – 0.58',
      'Main effects only. Too thin for subgroups.'],
     ['200', '0.07 – 0.18', '0.21 – 0.51', 'Workable. One subgroup split at a push.'],
     ['300', '0.06 – 0.15', '0.17 – 0.41',
      'Recommended. Comfortable main model, two subgroups.'],
     ['400', '0.05 – 0.13', '0.15 – 0.36',
      'Buys precision, not new capability, unless more subgroups are wanted.']],
    widths=[3.4, 3.6, 4.6, 4.6])
body('At 300 completed interviews the least precisely estimated parameter is the opt-out '
     'constant (standard error 0.148), and every service attribute is estimated to within '
     '0.06 to 0.10. Effects of the size normally seen in childcare choice experiments are '
     'comfortably detectable.')

h2('5.2  Cross-check against the standard rule')
body('The Johnson and Orme rule of thumb requires n ≥ 500c / (t × a), where c is the largest '
     'number of levels on any attribute (4 here), t is the number of tasks (6) and a is the '
     'number of service alternatives per task (2). That gives 167 traders for main effects — '
     'consistent with the design-based calculation above, and comfortably below 300.')

h2('5.3  The number that actually binds is the subgroups')
body('A subgroup you intend to model separately needs to satisfy that requirement on its own, '
     'not as a share of the total. That is what decides the sample, not the main model.')
tbl(['Subgroup you want to analyse separately', 'Traders needed', 'Implication at N = 300'],
    [['Women traders (the primary population)', '~167', 'Met, if women are ~60% or more of the sample'],
     ['Men traders', '~167', 'NOT met unless men are deliberately over-sampled'],
     ['Traders with a disability, or with a child with a disability', '~167',
      'Will not be met by chance. Needs purposive recruitment.'],
     ['Individual markets (6 of them)', '~167 each', 'Not achievable and should not be attempted']],
    widths=[6.4, 3.0, 6.8])
action('Decide now which subgroups must be reported separately. If the men–women comparison '
       'is required, 300 is not enough for both: either raise to about 400 with a quota, or '
       'accept that men are described but not modelled. If traders with disabilities are to '
       'be analysed rather than described, they need purposive recruitment on top of the '
       'main sample.')

h2('5.4  Our recommendation')
tbl(['', 'Number', 'Note'],
    [['Completed interviews', '300',
      'Target. 50 per market across 6 markets.'],
     ['Traders to approach', '~360',
      'Allowing for roughly 15% refusal and screen-out. The pilot screened on B12/B13, so '
      'budget for traders who do not qualify.'],
     ['Minimum women', '200', 'Keeps the primary population comfortably modellable.'],
     ['Men', '100', 'Described and compared descriptively; not modelled separately.'],
     ['Purposive disability sample', '40–60',
      'On top of the 300, recruited through OPDs, so objective iii can be analysed rather '
      'than only described.'],
     ['Choice tasks generated', '1,800', '300 traders x 6 cards.']],
    widths=[4.4, 2.6, 9.2])

page_break()
h1('6.  What happens next')
tbl(['#', 'Action', 'Who', 'Before'],
    [['1', 'Correct the Kobo form: rotation, block code, straight-line flag, level wording',
      'Data team', 'Any further interviews'],
     ['2', 'Load the 18-card design into the form', 'Data team', 'Any further interviews'],
     ['3', 'Confirm whether "1 untrained helper per 10 children" and "no special '
           'accommodation" are lawful', 'County regulatory interview', 'Design is frozen'],
     ['4', 'Re-pilot the DCE only, 15–20 traders, to confirm rotation works', 'Field team',
      'Full launch'],
     ['5', 'Decide the subgroup question in 5.3', 'Client', 'Sampling plan is fixed'],
     ['6', 'Write the provider interview guide', 'Study team', 'Costing can be completed'],
     ['7', 'Fill the costing template with real figures', 'Study team + County',
      'Objective iv can be answered']],
    widths=[0.9, 7.6, 3.8, 3.9])
body('Item 4 is worth the two days. The rotation fix is the one change we cannot verify from '
     'existing data — it has to be observed working.', after=8)

h2('A note on what this pilot cost and returned')
body('Twenty-three interviews found a confound that would have rendered the willingness-to-pay '
     'estimate from 300 interviews uninterpretable, and would probably not have been noticed '
     'until analysis. That is the pilot working exactly as intended. The corrections are '
     'modest; the alternative was a full survey whose central number could not be defended.')

h2('Sources')
body('All figures in this note come from the 23 pilot submissions exported from Kobo on 20 '
     'September 2026, re-analysed in R. The analysis is reproducible: '
     'Pilot_DCE_FollowUp_Analysis.Rmd with pilot_dce_analysis.R, dce_long.csv and '
     'respondents.csv. The choice model is a conditional logit fitted directly in base R, so '
     'no package versions affect the results.', size=10)

add_footer()
doc.save(OUT)
print('saved', OUT)
