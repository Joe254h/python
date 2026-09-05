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
OUT = '/home/user/python/output/Trader_Questionnaire_UasinGishu_Childcare_v2.docx'

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

# ================================================================ COVER
p = doc.add_paragraph('TRADER QUESTIONNAIRE', style='Title')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Designing Gender-Responsive Childcare Services in Uasin Gishu County Markets: '
     'Policy Options from a Decision-Focused Evaluation',
     size=13, bold=True, color=STEEL, after=2).alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Version 2.0  ·  Quantitative survey of market traders  ·  Target sample n = 300',
     size=10, italic=True, color=GREY, after=14).alignment = WD_ALIGN_PARAGRAPH.CENTER

h2('How this version differs from the reviewed draft')
instr('All reviewer recommendations marked for adoption have been applied in the body of the '
      'instrument. Questions are numbered sequentially within each section (A1, A2, A3 …) and '
      'every skip instruction has been updated to the new numbers. Yes/No/Don’t know/Refused '
      'items now use one consistent code set throughout: 1 = Yes, 2 = No, 3 = Don’t know, '
      '4 = Refused. Wording that the reviewer did not flag is unchanged. No original question '
      'has been lost — every item that was replaced, together with the reason, is recorded in '
      'Annex A: Review log.')

h2('Structure')
t = table(11, 3, widths=[2.2, 7.4, 6.6])
fill_header(t, ['Section', 'Content', 'Items'])
rows = [
    ('Consent', 'Participant consent form and re-contact permission', 'CF1'),
    ('A', 'Identification & consent', 'A1 – A10'),
    ('B', 'Respondent & work', 'B1 – B24'),
    ('C', 'Children & current care arrangements', 'C1 – C13'),
    ('D', 'Awareness of existing provision', 'D1 – D6'),
    ('E', 'Service attributes & barriers', 'E1 – E5'),
    ('F', 'Discrete choice experiment', 'F1 – F9'),
    ('G', 'Willingness to pay', 'G1 – G7'),
    ('H', 'Inclusion', 'H1 – H14'),
    ('I', 'Concerns on childcare', 'I1'),
]
for i, (a, b, c) in enumerate(rows, start=1):
    _cell_text(t.rows[i].cells[0], a, bold=True)
    _cell_text(t.rows[i].cells[1], b)
    _cell_text(t.rows[i].cells[2], c)
para('Section J: Close (J1 – J3)  ·  Annex A: Review log  ·  Annex B: Old-to-new numbering map',
     size=10, italic=True, color=GREY, before=4)

t = table(2, 4, widths=[4.0, 4.0, 4.0, 4.2])
fill_header(t, ['Respondent ID', 'Market', 'Date', 'Enumerator ID'])
for c in t.rows[1].cells:
    _cell_text(c, ' ')
    c.paragraphs[0].paragraph_format.space_after = Pt(8)

page_break()

# ================================================================ CONSENT
h1('Participant consent form')
instr('To be read aloud, in full, to every respondent — including those who can read it '
      'themselves — in the language they are most comfortable with.')

para('Hello, my name is __________________. We are researchers working with the Uasin Gishu '
     'County Government on a study about childcare and market trading in this county. We would '
     'like to ask you some questions about your household, your work, and your childcare needs '
     'and preferences. It will take about ___________ minutes. Taking part is voluntary. You do '
     'not have to answer any question you don’t want to, and you can stop at any time — this '
     'will not affect your trading permit, your stall, or any service you receive from the '
     'County. Some questions may feel personal; you’re free to skip those. Your name will not '
     'be written on the questionnaire, and your answers will be kept confidential. Your answers '
     'will be combined with those of other traders and reported only as group findings; no '
     'individual will be identifiable in any report. Your answers will be used only for this '
     'research and for informing County policy on market childcare.', after=6)

para('The information you provide will be used for research purposes and may be shared as '
     'anonymised or de-identified data through an appropriate open-access research data '
     'repository. The anonymised data may be used by other researchers for legitimate research '
     'and educational purposes. By consenting to participate, you agree to the use and sharing '
     'of your anonymised research data in this manner.', after=6)

para('If you have questions later, or wish to withdraw your answers, contact: 0721933701', after=2)
para('Principal Investigator: ____________________   Telephone: ____________________   '
     'Email: ____________________', after=8)
para('Do you have any questions? Do you agree to take part in this survey/interview?',
     bold=True, after=8)

para('Respondent’s name (printed) OR mark with an X if unable to write, then sign/thumbprint below:',
     size=10.5, after=6)
t = table(4, 2, widths=[5.0, 11.2])
for i, lab in enumerate(['Name', 'Signature / thumbprint', 'Date', 'Respondent ID code']):
    _cell_text(t.rows[i].cells[0], lab, bold=True)
    _cell_text(t.rows[i].cells[1], ' ')
    t.rows[i].cells[1].paragraphs[0].paragraph_format.space_after = Pt(6)

para('Witness — required only if the respondent gave oral consent via thumbprint/mark:',
     size=10.5, bold=True, before=8, after=6)
t = table(2, 2, widths=[5.0, 11.2])
for i, lab in enumerate(['Witness name', 'Witness signature']):
    _cell_text(t.rows[i].cells[0], lab, bold=True)
    _cell_text(t.rows[i].cells[1], ' ')
    t.rows[i].cells[1].paragraphs[0].paragraph_format.space_after = Pt(6)

para('Interviewer: I confirm I read this form in full and the respondent agreed voluntarily.',
     size=10.5, bold=True, before=8, after=6)
t = table(2, 2, widths=[5.0, 11.2])
for i, lab in enumerate(['Interviewer name', 'Signature']):
    _cell_text(t.rows[i].cells[0], lab, bold=True)
    _cell_text(t.rows[i].cells[1], ' ')
    t.rows[i].cells[1].paragraphs[0].paragraph_format.space_after = Pt(6)

q('CF1.', 'May the study team contact you about a later group discussion or clarification?', YN)
instr('If yes, record the telephone number on a separate re-contact sheet linked only by '
      'respondent ID. This keeps contact details separate from research responses and better '
      'protects confidentiality.')

page_break()

# ================================================================ SECTION A
h1('Section A — Identification & consent')
t = table(6, 2, widths=[6.2, 10.0])
fill_header(t, ['Item', 'Record here'])
for i, (n, lab) in enumerate([
        ('A1.', 'Enumerator ID'), ('A2.', 'Date (dd/mm/yyyy)'),
        ('A3.', 'Market name'), ('A4.', 'Section / zone within market'),
        ('A5.', 'Stall / interview GPS (if permitted)')], start=1):
    _cell_text(t.rows[i].cells[0], n + '  ' + lab, bold=False)
    t.rows[i].cells[0].paragraphs[0].runs[0].font.bold = False
    _cell_text(t.rows[i].cells[1], ' ')
    t.rows[i].cells[1].paragraphs[0].paragraph_format.space_after = Pt(5)

q('A6.', 'Consent read to the participant and given?', '1 = Yes    2 = No')
filt('If A6 = 2 → END the interview.')

q('A7.', 'Are you a trader in this market (own account or employed at a stall)?',
  '1 = Own account    2 = Employed by stall owner    3 = Casual / porter    4 = Other ____________')

q('A8.', 'On the days you trade in this market, are you responsible for the care of children '
         'aged 0–3 years?', YN)
instr('Adopted from reviewer item A8-R. This fixes the principal childcare population at ages 0–3 '
      'and links eligibility directly to care responsibilities on market days. See Annex A.')

q('A8a.', 'If A8 = 1: How many children aged 0–3 are you responsible for on market days?  '
          '________ children')

q('A9.', 'Do you have any child aged 0–8 in your care who has difficulty seeing, hearing, '
         'walking, communicating, learning, or self-care?', YN)
q('A9a.', 'If A9 = 1: How many such children?  ________ children')

filt('If A8 = 2 AND A9 = 2 → END (record as screen-out; keep the count for the prevalence '
     'denominator).')

q('A10.', 'In which language is this interview being conducted?',
  '1 = Kiswahili    2 = English    3 = Kalenjin    4 = Luhya    5 = Kikuyu    6 = Luo    '
  '7 = Other ____________')
instr('Added. The consent script promises the interview in the respondent’s preferred language; '
      'recording it allows that promise to be checked and lets analysis test for language effects.')

page_break()

# ================================================================ SECTION B
h1('Section B — Respondent & work')
h2('B(i)  Demographics')
q('B1.', 'Age (completed years)  ________')
q('B2.', 'Sex of respondent', '1 = Female    2 = Male    3 = Other / prefers not to say')
q('B3.', 'How many years have you been selling in this market?  ________ years')
q('B4.', 'Highest level of education completed',
  '1 = None   2 = Some primary   3 = Completed primary   4 = Some secondary   '
  '5 = Completed secondary   6 = Certificate   7 = Diploma   8 = Higher diploma   '
  '9 = Undergraduate   10 = Masters   11 = PhD')
q('B5.', 'Marital status',
  '1 = Married    2 = Single    3 = Separated    4 = Divorced    5 = Widowed')
q('B6.', 'If B5 = 1 (married): Who usually decides how your children under 3 are cared for '
         'while you are at the market?',
  '1 = Me alone   2 = My spouse   3 = We decide together   4 = Another family member decides   '
  '5 = Varies')
q('B7.', 'How many people live in your household in total (including yourself)?  ________')
q('B8.', 'Number of adults aged 18 years and above living in your household  ________')
q('B9.', 'Number of children under 18 living in your household  ________')
q('B10.', 'Are you the main income earner in your household?',
  '1 = Yes    2 = No    3 = Shared equally')
instr('B7, B9 and A10 are additions responding to the drafting note “check more questions on '
      'demographics based on the context”. Delete any the team does not need.')

h2('B(ii)  Trading pattern')
q('B11.', 'What do you sell / what work do you do here?',
  '1 = Fresh produce   2 = Cereals / dry goods   3 = Cooked food   4 = Gunny bags   '
  '5 = Household goods   6 = Porter / casual   7 = Other ____________')
q('B12.', 'How many people do you employ or have helping you at this stall, apart from '
          'yourself?  ________ people')
instr('Added in response to the drafting note “also employee you have in number”.')
q('B13.', 'How many days did you come to the market in the last 7 days?  ________  (0–7)')
q('B14.', 'In a normal week, how many days do you come?  ________  (0–7)')
q('B15.', 'What time do you usually arrive?  ________  am / pm')
q('B16.', 'What time do you usually leave?  ________  am / pm')
q('B17.', 'Are there months when you trade fewer days than usual?', YN)
q('B17a.', 'If B17 = 1: Which months? (tick all that apply)')
t = table(2, 12, widths=[1.35]*12)
months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
fill_header(t, months, size=9)
for c in t.rows[1].cells:
    _cell_text(c, '☐', align=WD_ALIGN_PARAGRAPH.CENTER, size=11)
q('B17b.', 'If B17 = 1: Roughly how many days a week do you trade in those months?  ________')

h2('B(iii)  Earnings')
q('B18.', 'On a normal trading day, about how much do you sell in total, before paying for '
          'anything?  KES ________', '4 = Refused')
instr('Added in response to the drafting note “question profit and sale”. B18 captures gross '
      'daily takings; B19 captures what is left after costs. Both are needed to interpret '
      'willingness to pay in Section G.')
q('B19.', 'On a normal trading day, after paying for stock, transport, market fees, helpers and '
          'other business expenses, about how much on average remains for you or your household?  '
          'KES ________', '4 = Refused')
instr('Adopted from reviewer item B19 (formerly B12-R). It provides a clearer affordability '
      'measure than earnings net of stock alone. See Annex A.')
q('B20.', 'Does your income vary a lot from day to day?',
  '1 = Very stable    2 = Somewhat stable    3 = Varies a lot')
q('B20a.', 'On your best days and your worst days, what do you take home?  '
           'Best: KES ________   Worst: KES ________')

h2('B(iv)  Childcare-related loss of trading time')
note('B21 is the productivity-loss estimate. Do not introduce any framing about the benefits of '
     'childcare before B21 or the estimate will inflate. B21–B24 must be asked before Section E.')
q('B21.', 'In the last 30 days, did you lose any trading days because you had to look after a '
          'child?', '1 = Yes    2 = No')
q('B21a.', 'If B21 = 1: How many days?  ________')
q('B21b.', 'If B21 = 1: What happened? (tick all that apply)',
  '1 = Arrived late   2 = Left early   3 = Missed a full trading day   '
  '4 = Brought a child to the market when you had not planned to   '
  '5 = Sent someone else to run the stall   6 = Closed the stall for part of the day   '
  '7 = Other ____________')
q('B21c.', 'If B21 = 1: About how much income did you lose because of these disruptions?  '
           'KES ________', '3 = Don’t know    4 = Refused')
q('B22.', 'In one sentence, please describe the biggest challenge you currently face in your '
          'business.  (open question)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('B23.', 'What are the main problems, if any, with the childcare arrangement you currently use? '
          '(tick all that apply, then ask which is the single main problem)',
  '1 = Cost   2 = Unreliable caregiver   3 = Distance   4 = Unsuitable hours   5 = Safety   '
  '6 = Poor quality of care   7 = Child not accepted   8 = No problem   9 = Other ____________')
q('B23a.', 'Which of these is the single main problem?  ________  (enter one code from B23)')
q('B24.', 'In the last 30 days, was there any day when you needed childcare but could not obtain '
          'a safe and acceptable arrangement?', YNDK)
q('B24a.', 'If B24 = 1: On how many of the last 30 days did this happen?  ________ days')

page_break()

# ================================================================ SECTION C
h1('Section C — Children & current care arrangements')
q('C1.', 'How many children aged 0–3 years are in your care?  ________')
q('C2.', 'How many children aged 0–8 years in your care live with a disability — that is, they '
         'have difficulty seeing, hearing, walking, communicating, remembering or concentrating, '
         'or with self-care?  ________')
instr('C2 replaces the unlabelled duplicate roster in the draft (“how many children do you have '
      'aged 0-8 and they live with disability — frame well this part”). The two rosters are now '
      'one child list: enter every child from C1 and every child from C2 in the grid below, '
      'listing each child only once.')
filt('Complete one column for each child listed in C1 and C2. Cap the roster at 4 children. '
     'If a child qualifies under both C1 and C2, list the child once and code C6 = 3.')

hdr = ['Item', 'Child 1', 'Child 2', 'Child 3', 'Child 4']
rowspecs = [
    ('C3.  Child line number', ''),
    ('C4.  Date of birth (dd/mm/yyyy)', ''),
    ('C5.  Sex   1 = Male   2 = Female', ''),
    ('C6.  Child listed under\n1 = C1 (aged 0–3)   2 = C2 (0–8, disability)   3 = Both', ''),
    ('C7.  Where is this child while you are at the market? (primary arrangement)\n'
     '1 = With me at the stall   2 = Left at home alone   3 = Left at home with older sibling '
     '(under 18)   4 = Left at home with adult family member   5 = Left with neighbour / friend '
     '(unpaid)   6 = Paid house help at home   7 = Paid informal daycare in the estate / outside '
     'the market   8 = Registered daycare / ECD centre   9 = Other ____________', ''),
    ('C8.  If C7 = 6, 7 or 8: How much do you pay?  KES ________ per month', ''),
    ('C9a. If C7 = 7 or 8: Minutes from your home to the childcare place', ''),
    ('C9b. If C7 = 7 or 8: Minutes from your stall to the childcare place', ''),
    ('C10. If C7 = 1: Where exactly does the child stay during the day?\n'
     '1 = On / under the stall   2 = Playing in market walkways   3 = Tied on my back   '
     '4 = Other ____________', ''),
    ('C11. In the last 3 months, has this child had any of the following while you were working? '
     '(tick all that apply)\na = Illness needing treatment   b = Injury   c = Went missing   '
     'd = Wandered off   e = None of these   3 = Don’t know', ''),
    ('C11a. For each event ticked in C11, how many times in the last 3 months?\n'
     'a ____   b ____   c ____   d ____', ''),
    ('C11b. What action did you take on the most recent occasion? (open question, then code)', ''),
]
t = table(len(rowspecs) + 1, 5, widths=[7.6, 2.15, 2.15, 2.15, 2.15])
fill_header(t, hdr)
for i, (lab, _) in enumerate(rowspecs, start=1):
    _cell_text(t.rows[i].cells[0], lab, size=9)
    for j in range(1, 5):
        _cell_text(t.rows[i].cells[j], ' ', size=9)
        t.rows[i].cells[j].paragraphs[0].paragraph_format.space_after = Pt(4)
instr('C11a and C11b replace the draft item “C8a-R. From the above how many times? … what action '
      'was taken?”, which was flagged for reframing. Counts are now recorded per event type and '
      'the action taken is a separate, codeable item.')

h2('C12.  Washington Group / UNICEF Child Functioning — one grid per child aged 2 and above')
instr('Use the exact wording below. Do not paraphrase. Read: “Compared with children of the same '
      'age, does [NAME] have difficulty …”')
domains = ['(a)  seeing, even if wearing glasses',
           '(b)  hearing, even if using a hearing aid',
           '(c)  walking or climbing steps',
           '(d)  remembering or concentrating',
           '(e)  with self-care such as washing all over or dressing',
           '(f)  communicating, for example understanding or being understood']
scale = ['1\nNo difficulty', '2\nSome difficulty', '3\nA lot of difficulty', '4\nCannot do at all']
for child in range(1, 3):
    para('Child %d' % child, size=10.5, bold=True, color=STEEL, before=6, after=2, indent=0)
    t = table(len(domains) + 1, 5, widths=[7.6, 2.15, 2.15, 2.15, 2.15])
    fill_header(t, ['Compared with children of the same age, does [NAME] have difficulty …'] + scale, size=9)
    for i, d in enumerate(domains, start=1):
        _cell_text(t.rows[i].cells[0], d, size=9.5)
        for j in range(1, 5):
            _cell_text(t.rows[i].cells[j], '☐', size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
instr('Reproduce this grid for Child 3 and Child 4 where the roster has four children.')

h2('C13.  Washington Group Short Set — the respondent')
instr('Use the exact wording below. Do not paraphrase. Read: “[NAME], do you have difficulty …”')
t = table(len(domains) + 1, 5, widths=[7.6, 2.15, 2.15, 2.15, 2.15])
fill_header(t, ['[NAME], do you have difficulty …'] + scale, size=9)
for i, d in enumerate(domains, start=1):
    _cell_text(t.rows[i].cells[0], d, size=9.5)
    for j in range(1, 5):
        _cell_text(t.rows[i].cells[j], '☐', size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
note('C12 and C13 are the filters for Section H. C12 gates H6–H13; C13 gates H1–H5.')

page_break()

# ================================================================ SECTION D
h1('Section D — Awareness of existing provision')
q('D1.', 'Do you know of any childcare space or daycare inside the market?', YN)
filt('If D1 = 2 → skip to D6.')
q('D2.', 'Is it currently operating?',
  '1 = Yes, operating    2 = Exists but closed / unused    3 = Under construction    '
  '4 = Don’t know')
q('D3.', 'Have you ever used it?',
  '1 = Yes, currently    2 = Yes, in the past    3 = Never')
q('D4.', 'If D3 = 2: Why did you stop?  (open question)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('D5.', 'If D3 = 3: Why have you never used it?  (open question, then code)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('D6.', 'Have you heard of any county government plan to provide childcare in markets?', YN)

page_break()

# ================================================================ SECTION E
h1('Section E — Service attributes & barriers')
q('E1.', 'Suppose a good childcare space were available in this market. How important would '
         'each of these be to you?')
instr('Read each attribute and tick one box per row. Every row must be answered.')
attrs = [
    ('a', 'Cost'),
    ('b', 'Very close to my stall (I can check on the child)'),
    ('c', 'Opens before I arrive and closes after I leave'),
    ('d', 'Caregivers are trained and hold a certificate'),
    ('e', 'Few children per caregiver'),
    ('f', 'Food / porridge provided'),
    ('g', 'Clean toilet and washing water'),
    ('h', 'Locked / secure, controlled entry'),
    ('i', 'Somebody I can hold responsible if something goes wrong'),
    ('j', 'Takes babies in the range of 0 to 3 years'),
    ('k', 'Takes children with disabilities'),
    ('l', 'I can pay daily rather than monthly'),
]
escale = ['1\nNot important', '2\nSomewhat important', '3\nVery important',
          '4\nWould not use it without this']
t = table(len(attrs) + 1, 6, widths=[0.9, 6.7, 2.15, 2.15, 2.15, 2.15])
fill_header(t, ['', 'Attribute'] + escale, size=9)
for i, (ltr, txt) in enumerate(attrs, start=1):
    _cell_text(t.rows[i].cells[0], ltr, bold=True, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    _cell_text(t.rows[i].cells[1], txt, size=9.5)
    for j in range(2, 6):
        _cell_text(t.rows[i].cells[j], '☐', size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

q('E2.', 'What would stop you from using such a space?  (tick all that apply — do not read the list)',
  '1 = Cost   2 = Don’t trust strangers with my child   3 = Family / husband would object   '
  '4 = Child too young   5 = Worry about disease or infection   6 = Too far from stall   '
  '7 = Hours don’t match mine   8 = My child has needs they can’t handle   9 = I don’t need it   '
  '10 = Other ____________')
q('E2a.', 'Of those ticked, which is the single main reason?  ________  (enter one code from E2)')

q('E3.', 'If a market childcare service were available, what schedule and location would you '
         'need?')
instr('Ask all four parts. This is the exact service-design requirement; E1 only rates its '
      'importance.')
t = table(5, 2, widths=[7.0, 9.2])
fill_header(t, ['Requirement', 'Record here'])
for i, lab in enumerate([
        'E3a.  Which days of the week would you need it? (tick all: Mon Tue Wed Thu Fri Sat Sun)',
        'E3b.  What opening time would suit you?',
        'E3c.  What closing time would suit you?',
        'E3d.  Farthest acceptable travel time from your stall (minutes)'], start=1):
    _cell_text(t.rows[i].cells[0], lab, size=9.5)
    _cell_text(t.rows[i].cells[1], ' ', size=9.5)
    t.rows[i].cells[1].paragraphs[0].paragraph_format.space_after = Pt(5)

q('E4.', 'Who should have primary responsibility for each of the following?')
instr('Read each function and record ONE code per row. Do not read the code list — probe until '
      'the respondent names a single body for that function.')
funcs = [
    'Setting the standards the centre must meet',
    'Operating the centre day to day',
    'Employing and paying the caregivers',
    'Training the caregivers',
    'Inspecting safety and hygiene',
    'Receiving and resolving complaints',
    'Paying for major repairs and maintenance',
    'Setting and collecting the fees',
    'Deciding which children may enrol',
    'Making sure the space is accessible to children and parents with disabilities',
    'Covering the cost if fees do not meet the running cost',
]
cols = ['1\nCounty govt', '2\nPrivate operator', '3\nMarket committee', '4\nParent committee',
        '5\nNational govt', '6\nPublic–private partnership', '7\nOther', '8\nDon’t know']
t = table(len(funcs) + 1, 9, widths=[5.0, 1.4, 1.4, 1.4, 1.4, 1.4, 1.55, 1.3, 1.3])
fill_header(t, ['Function'] + cols, size=8)
for i, f in enumerate(funcs, start=1):
    _cell_text(t.rows[i].cells[0], f, size=9)
    for j in range(1, 9):
        _cell_text(t.rows[i].cells[j], '☐', size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
q('E4a.', 'If “Other” was recorded for any function, specify which function and who:  '
          '____________________________________________')
instr('E4 is the expanded version of the reviewer item E3-R. Splitting responsibility into '
      'eleven separate functions is what produces evidence on accountability under each of the '
      'four delivery models. Analyse it as a function-by-actor matrix, not as a single score.')

q('E5.', 'If your child were mistreated or injured at the facility, who would you complain to?  '
         '(open question, then code)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
note('E4 and E5 are the governance questions traders can answer. Do not add a “which management '
     'model do you prefer” item here — model preference is measured by the choice experiment in '
     'Section F, where every respondent has first heard the same standardised description of all '
     'four models (show-card F0).')

page_break()

# ================================================================ SECTION F
h1('Section F — Discrete choice experiment')
para('Field instrument — pilot version (n = 30).  Uasin Gishu market childcare study.',
     size=10, italic=True, color=GREY, after=6)

h2('F0.  Model description show-card — read once, before Set 1')
instr('Read all four descriptions aloud, in the same order and the same tone, before the first '
      'choice set. Every respondent must hear the same description. Do not add examples of your '
      'own and do not indicate which model the County favours.')
mrows = [
    ('County-run',
     'The County owns and runs the space.',
     'County staff, employed by the County',
     'The County sets the fee',
     'The county office',
     'The County pays',
     'The County'),
    ('Private operator',
     'A private business rents the space from the County and runs it.',
     'Employed by the operator',
     'The operator sets the fee',
     'The operator',
     'The operator pays, under the rental agreement',
     'The operator'),
    ('Public–private partnership',
     'The County and a private operator run it jointly under an agreement.',
     'Employed by the operator, to County standards',
     'The County and operator agree the fee jointly',
     'A joint office',
     'Shared, as set out in the agreement',
     'The County and operator jointly'),
    ('Market-trader committee',
     'The traders’ own committee runs the space.',
     'Hired by the committee',
     'The committee sets the fee',
     'The committee',
     'The committee raises the money',
     'The committee'),
]
t = table(len(mrows) + 1, 7, widths=[2.5, 3.4, 2.5, 2.4, 1.9, 2.4, 1.9])
fill_header(t, ['Model', 'How it works', 'Caregivers', 'Who sets the fee',
                'Complaints go to', 'Major repairs', 'Accessibility duty'], size=8)
for i, r in enumerate(mrows, start=1):
    _cell_text(t.rows[i].cells[0], r[0], bold=True, size=9)
    for j in range(1, 7):
        _cell_text(t.rows[i].cells[j], r[j], size=8.5)
instr('This show-card is the "in-depth characteristics of each model" note in the reviewed draft. '
      'Its columns deliberately mirror the “Who runs it” attribute levels used on the choice '
      'cards and the functions listed in E4, so that the three sources can be read together.')

h2('F0a.  Design specification')
para('Seven attributes: cost, location, opening hours, caregiver ratio and training, food, '
     'operator / accountability, and inclusion. Two unlabelled alternatives plus an opt-out '
     '(“I would use neither; I’d keep my current arrangement”). D-efficient design, 12 choice '
     'sets blocked into 2 blocks of 6 per respondent. Generate in R (idefix or support.CEs) or '
     'Ngene.', size=10, after=4)
para('This pilot design uses assumed attribute priors, not priors estimated from data. Pilot the '
     'cards with 30 respondents, check for non-trading (always choosing on one attribute) and '
     'left–right bias, estimate preliminary preferences, and regenerate the final D-efficient '
     'design before printing the main-survey version. Use only levels that satisfy minimum '
     'legal, safety and accessibility requirements in the final design.',
     size=10, after=4)
note('The pilot cards below still contain the levels “1 untrained helper per 10 children” and '
     '“no special accommodation for children with disabilities”. They are reproduced here '
     'unchanged so the pilot runs on the design as drafted. If these levels fall below the '
     'minimum standards confirmed by the county (KII section 1), drop them when the design is '
     'regenerated after the pilot.')

h2('F0b.  Cheap-talk script — read once, before Set 1 only')
para('“People often say they would pay more for something than they actually do when the time '
     'comes. Please answer as if this money were really coming out of today’s sales.”',
     size=11, italic=True, after=4, indent=0)
instr('Read this once, out loud, immediately before the first card — not before every set. '
      'Without it a trader may agree to a price because no money is actually leaving her pocket; '
      'with it she is more likely to weigh the amount against today’s takings.')

h2('F0c.  Reading instructions')
bullet('Sets 1–2: read every attribute aloud in full for both alternatives, pointing at each icon '
       'on the show-card as you name it.', size=10)
bullet('Sets 3–6: point at the card and give the short headline for each attribute — the card '
       'carries the detail from here.', size=10)
bullet('Every set includes a third option: “I would use neither; I’d keep my current '
       'arrangement.” Read it every time, at the same point in the sequence and in the same tone '
       'as the two alternatives. If you read A and B carefully but rush “or neither”, '
       'respondents learn that “neither” is not a real option and you will get fewer honest '
       'opt-outs than you should.', size=10)
para('Example, same set, both styles:', size=10, italic=True, color=GREY, before=4, after=2)
bullet('Full (sets 1–2): “Option A costs 60 shillings a day. It’s a 5-minute walk from your '
       'stall. It’s open from 7 in the morning to 5 in the evening. There’s one trained '
       'caregiver for every 10 children. They provide porridge and lunch. It’s run by the county '
       '— if you have a problem, you go to the county office. There’s no special accommodation '
       'for children with disabilities.”', size=10)
bullet('Short (sets 3–6): “Option A: 60 shillings, 5-minute walk, 7 to 5, one caregiver per ten, '
       'food provided, county-run, no accommodation.”', size=10)

h2('F0d.  Assigning respondents to a block')
para('Each respondent answers ONE block of 6 sets, not both. Alternate by respondent ID: '
     'odd-numbered IDs answer Block 1, even-numbered IDs answer Block 2. The set numbers F1–F6 '
     'are the same variables in both blocks; the block number records which card set was shown.',
     size=10, after=4)

# ---- reproduce the 12 choice cards from the source document -------------
NORM = {
    'Who runs it / who you go to with a problem': 'Who runs it',
    'county and operator jointly agree on fees; complaints go to a joint office':
        'County and private operator jointly agree on fees; complaints go to a joint office',
    'County and operator jointly agree on fees; complaints go to a joint office':
        'County and private operator jointly agree on fees; complaints go to a joint office',
    'County and operator jointly agree fees; complaints go to a joint office':
        'County and private operator jointly agree on fees; complaints go to a joint office',
    'county and operator jointly agree fees; complaints go to a joint office':
        'County and private operator jointly agree on fees; complaints go to a joint office',
    'County and private operator jointly agree fees; complaints go to a joint office':
        'County and private operator jointly agree on fees; complaints go to a joint office',
}
def norm(s):
    s = ' '.join(s.split())
    return NORM.get(s, s)

cards = []
for tb in src.tables[2:14]:
    card = []
    for row in tb.rows:
        card.append([norm(c.text) for c in row.cells])
    cards.append(card)
assert len(cards) == 12, len(cards)

blocks = [('Block 1', cards[0:6], [1, 3, 5, 7, 9, 11]),
          ('Block 2', cards[6:12], [2, 4, 6, 8, 10, 12])]
for bname, bcards, dsets in blocks:
    page_break()
    h2('%s — show to respondents with %s-numbered IDs'
       % (bname, 'odd' if bname.endswith('1') else 'even'))
    for k, (card, ds) in enumerate(zip(bcards, dsets), start=1):
        h3('F%d.   Set %d of 6   (design set %d)' % (k, k, ds))
        t = table(len(card), 3, widths=[4.3, 6.0, 6.0])
        fill_header(t, card[0], size=9)
        for i in range(1, len(card)):
            _cell_text(t.rows[i].cells[0], card[i][0], bold=True, size=9)
            _cell_text(t.rows[i].cells[1], card[i][1], size=9)
            _cell_text(t.rows[i].cells[2], card[i][2], size=9)
        p = para('Which would you choose?     ☐ 1 = Alternative A      ☐ 2 = Alternative B      '
                 '☐ 3 = Neither — I’d keep my current arrangement',
                 size=10, bold=True, before=3, after=8)

page_break()
h2('Enumerator checks — ask after the last set')
q('F7.', 'Non-trading check: did the respondent pick the cheapest alternative in every single '
         'set of their block, even where the quality gap looked large?', YN)
instr('This is not necessarily an error, but flag it on the respondent’s cover sheet for review.')
q('F8.', 'Opt-out check: did the respondent pick “Neither” in every set?', YN)
q('F8a.', 'If F8 = 1, ask: “Can you tell me why you would keep your current arrangement rather '
          'than any of these?”  Record verbatim.')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('F9.', 'Attribute non-attendance: “Was there any part of these cards — the cost, the distance, '
         'the hours, the caregivers, the food, who runs it, or the accessibility — that you '
         'ignored when choosing?”  (tick all that were ignored)',
  '1 = Cost   2 = Location   3 = Opening hours   4 = Caregiver ratio / training   5 = Food   '
  '6 = Who runs it   7 = Inclusiveness   8 = None ignored')

page_break()

# ================================================================ SECTION G
h1('Section G — Willingness to pay')
filt('Ask Section G AFTER the choice experiment, never before.')
q('G1.', 'Payment card.')
para('Read: “Here are some amounts per child per day. For a childcare space inside the market, '
     'open 6:00–19:00, with one trained caregiver for every 10 children, porridge and lunch '
     'provided, run by county staff (complaints go to the county office), with a ramp, a toilet, '
     'and staff trained to support children with disabilities — for each amount, tell me whether '
     'you would definitely use it, might use it, or would not use it.”',
     size=10.5, italic=True, indent=1.05, after=5)
instr('Tick one box on every row. Work down the list in order; do not skip amounts.')
amounts = [20, 30, 50, 70, 100, 130, 150, 200, 250]
t = table(len(amounts) + 1, 4, widths=[4.0, 4.05, 4.05, 4.05])
fill_header(t, ['Price per child per day', '1\nDefinitely use it', '2\nMight use it',
                '3\nWould not use it'], size=9)
for i, a in enumerate(amounts, start=1):
    _cell_text(t.rows[i].cells[0], 'KES %d' % a, bold=True, size=10)
    for j in range(1, 4):
        _cell_text(t.rows[i].cells[j], '☐', size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

q('G2.', 'What is the most you would pay per day for that service?  KES ________')
q('G3.', 'If B5 = 1 (married): Would you decide and pay this amount yourself, or would you need '
         'to discuss it with your spouse first?',
  '1 = Decide / pay myself   2 = Would discuss and agree together   '
  '3 = Spouse / partner would decide   4 = Don’t know')
q('G4.', 'Would you rather pay',
  '1 = Per day    2 = Per week    3 = Per month    4 = Per month with a discount')
q('G5.', 'If you have more than one child aged 0–3: Would you pay the same amount for a second '
         'child, or would you need a lower price?',
  '1 = Same amount    2 = Lower fee; specify KES ________    3 = Would enrol only one child')
q('G6.', 'If you have more than one child aged under 8 years living with a disability: Would you '
         'pay the same amount for the second child, need a lower fee, or enrol only one child?',
  '1 = Same amount    2 = Lower fee; specify KES ________    3 = Would enrol only one child')
q('G7.', 'If the price were the amount you gave in G2, how many days per week would you use it?  '
         '________  (0–7)')
note('G2 and the DCE cost coefficient both capture individual stated willingness to pay. Neither '
     'confirms that the household will actually authorise and hand over that money day to day. '
     'Cross-tabulate G2 by G3 before treating the WTP figure as a usable price point: if a large '
     'share of respondents who state a high G2 also report needing spousal agreement, the '
     'effective household willingness to pay may sit below the individually stated one. '
     '(The draft note referred to “B5a”, which does not exist in the instrument; the '
     'authorisation item is G3.)')

page_break()

# ================================================================ SECTION H
h1('Section H — Inclusion')
instr('These questions ask about experiences of exclusion and disability. Keep your tone '
      'matter-of-fact. If a respondent becomes upset, pause and do not press for detail they do '
      'not offer.')

h2('H(i)  The respondent’s own access — H1 to H5')
filt('Ask H1–H5 only if C13 records “a lot of difficulty” or “cannot do at all” in any domain. '
     'Otherwise skip to H6.')
q('H1.', 'Getting from your home to this market — what makes it difficult?  (open question)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('H2.', 'Moving around inside the market — what makes it difficult?  (open question)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('H3.', 'If a childcare space were here, what would you need in order to be able to drop off '
         'and collect your child yourself?  (open question)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('H4.', 'Have you ever been refused a service, or treated badly, at a facility because of your '
         'disability?', '1 = Yes    2 = No    4 = Refused')
instr('If yes, prompt gently once: “Can you tell me a little about that?” Do not press further '
      'if the respondent does not continue.')
para('_' * 92, size=10, indent=1.05, after=6)
q('H5.', 'What communication format would make it easiest for you to receive information, give '
         'consent, or make a complaint about the childcare service?',
  '1 = Standard print   2 = Large print   3 = Sign language   4 = Audio   '
  '5 = Pictorial / easy-read   6 = Help from a trusted person   7 = Other ____________')

h2('H(ii)  The child’s needs — H6 to H13')
filt('Ask H6–H13 only if any child is flagged in C12. Otherwise skip to H14.')
q('H6.', 'Has any childcare provider or school ever refused to take this child?', YNDR)
q('H7.', 'If H6 = 1: What reason were you given?  (open question)')
para('_' * 92, size=10, indent=1.05, after=6)
q('H8.', 'What would a childcare space need to have, for you to leave this child there?  '
         '(open question, then code — tick all that apply)',
  '1 = Trained caregiver   2 = Fewer children per caregiver   3 = Ramp / accessible toilet   '
  '4 = Someone who can give medication or therapy   5 = Other children who won’t bully   '
  '6 = Close enough that I can come quickly   7 = Other ____________')
q('H9.', 'Does this child currently receive any therapy, assessment, or support service?', YNDR)
q('H9a.', 'If H9 = 1: Which?  (open question)')
para('_' * 92, size=10, indent=1.05, after=6)
q('H10.', 'What support would this child need from a caregiver during a normal childcare day?  '
          '(tick all that apply; probe only where relevant)',
  '1 = Communication   2 = Mobility   3 = Feeding   4 = Toileting   5 = Medication   '
  '6 = Behaviour support   7 = Sensory needs   8 = Therapy schedule   9 = Emergency response   '
  '10 = Other ____________')
q('H11.', 'What additional training or support would caregivers need before you would trust them '
          'to care for this child?  (open question, then code)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('H12.', 'What arrangement would allow this child to participate safely and comfortably with '
          'other children?',
  '1 = Same room with ordinary support   2 = Same room with additional individual support   '
  '3 = Access to a quiet or flexible support space when needed   '
  '4 = Another arrangement; specify ____________   5 = Don’t know')
q('H13.', 'Why would this arrangement work best for the child?  (open question)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)

h2('H(iii)  Barriers — ask all respondents')
q('H14.', 'Have any of the following made it difficult for you or your child to use childcare?  '
          '(tick all that apply)',
  '1 = Cost   2 = Stigma   3 = Negative attitudes   4 = Documentation requirements   '
  '5 = Transport   6 = Communication barriers   7 = Refusal to make an accommodation   '
  '8 = None of these   9 = Other ____________')
q('H14a.', 'Which of these is the single main barrier?  ________  (enter one code from H14)')

# ================================================================ SECTION I
h1('Section I — Concerns on childcare')
q('I1.', 'If you had a concern about the childcare service, how would you prefer to report it '
         'confidentially?',
  '1 = In person   2 = Telephone   3 = SMS / WhatsApp   4 = Suggestion or complaint box   '
  '5 = Through a representative or organisation   6 = Other ____________')

# ================================================================ SECTION J
h1('Section J — Close')
para('“Thank you for your time today — this has been really helpful. Before we finish, I have a '
     'couple of last questions.”', size=11, italic=True, after=6)
q('J1.', 'Would you be willing to take part in a group discussion later?', YN)
instr('If yes and CF1 was also yes, record the contact once only, on the separate re-contact '
      'sheet, linked by respondent ID.')
q('J2.', 'Contact (optional):  ______________________________________')
q('J3.', 'Enumerator observations  (open — complete after the respondent leaves; not read aloud)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)

# ================================================================ ANNEX A
page_break()
h1('Annex A — Review log')
para('No original questionnaire question has been deleted. Where the reviewed draft carried an '
     'original item and a recommended replacement, the item adopted into the body of this '
     'version is shown below alongside the original wording and the reason given. Items the '
     'reviewer did not flag were carried through unchanged.', size=10, after=8)
log = [
    ('A8', 'Do you have any child aged 0–3 currently in your care?',
     'Adopted A8-R as A8: “On the days you trade in this market, are you responsible for the care '
     'of children aged 0–3 years?” plus A8a for the count.',
     'The draft referred to children under five and children up to eight, so the eligibility age '
     'was not applied consistently. The replacement fixes the population at 0–3 and links '
     'eligibility to care responsibility on market days.'),
    ('B12', 'On a normal trading day, about how much money do you take home after paying for stock?',
     'Adopted B12-R as B19, and added B18 on gross daily sales.',
     'Money remaining after stock alone is not a reliable measure of disposable earnings because '
     'other business expenses are omitted. Asking gross takings and net earnings separately gives '
     'a clearer affordability measure for Section G.'),
    ('C8a-R', 'From the above how many times? … What action was taken?',
     'Reframed as C11a (count per event type over the last 3 months) and C11b (action taken on '
     'the most recent occasion, coded).',
     'Flagged in the draft for reframing: the original mixed a count and an open action question '
     'in one unnumbered item, and did not say which event the count referred to.'),
    ('C1–C4 duplicate roster', 'Two identical “C1 child number / C2 date of birth / C3 sex” '
     'blocks, the second introduced by “how many children do you have aged 0-8 and they live '
     'with disability — frame well this part”.',
     'Merged into one child roster: C1 counts children aged 0–3, C2 counts children aged 0–8 '
     'living with a disability, and C6 records which list each child belongs to.',
     'The duplicated block would have produced two partial rosters for the same household and '
     'double-counted any child qualifying on both criteria.'),
    ('D1', 'Do you know of any childcare space or daycare inside or next to this market? 1=Yes 0=No',
     'Now: “… inside the market?” with codes 1 = Yes, 2 = No.',
     'Wording and coding as revised by the study team on the final draft.'),
    ('E1 item j', 'Takes babies under 1 year',
     'Now: “Takes babies in the range of 0 to 3 years”.',
     'Revised by the study team to match the 0–3 eligibility definition.'),
    ('E1 layout', 'Attribute list with no response columns.',
     'Rebuilt as a 12-row rating grid with the four response options as columns.',
     'Requested on the final draft: “ensure the Likert is properly done, use the table”.'),
    ('E2a', 'Recommended addition on days, hours and maximum travel time.',
     'Adopted into the numbered sequence as E3, split into E3a–E3d.',
     'Requested on the final draft: “add this one in the list”. The draft rated proximity and '
     'hours but never obtained the exact schedule and location requirement needed for service '
     'design.'),
    ('E3', 'Who do you think should be responsible for making sure the childcare space is safe '
     'and well run? (single response)',
     'Replaced by E4: an eleven-function responsibility matrix with eight actor columns, '
     'including public–private partnership.',
     'A single response treats operating, regulating, inspecting and handling complaints as if '
     'they were the same responsibility. The final draft asked for the matrix form and for more '
     'responsibilities to be added so the matrix answers the governance objective.'),
    ('E5-R', 'After hearing the same standardised description of each option, which childcare '
     'operating model would you prefer?',
     'Removed by the study team on the final draft; not carried into this version.',
     'Model preference is measured by the choice experiment in Section F. Asking a stated model '
     'preference in Section E would also anchor the “Who runs it” attribute before the choice '
     'cards are shown.'),
    ('F0', 'Design note: “6 attributes”.',
     'Corrected to seven attributes (cost, location, hours, caregiver ratio/training, food, '
     'operator/accountability, inclusion) in F0a, and a model description show-card added as F0.',
     'The design note said six attributes but the cards carry seven. The final draft asked for '
     'the characteristics of each model to be set out in depth in line with the attributes.'),
    ('G1', 'Payment card as a single row of prices.',
     'Rebuilt as a 9-row rating grid, one row per price, three response columns.',
     'Requested on the final draft: “make it Likert”.'),
    ('G2b-R', 'Recommended replacement asking who must agree, for all respondents.',
     'Removed by the study team on the final draft; the original married-only filter is retained '
     'as G3, recoded 1–4.',
     'Study team decision. Note that willingness to pay is therefore only cross-checked against '
     'household authorisation for married respondents.'),
    ('G4 / G4-R', 'Alternative wordings of the sibling-price question.',
     'Both retained as distinct questions: G5 covers a second child aged 0–3, G6 a second child '
     'under 8 living with a disability.',
     'The final draft revised G4 to “under 3” and re-scoped G4-R to children under 8 with a '
     'disability, making them two different questions rather than alternatives.'),
    ('G6 (attribute uptake battery)', 'Would you be more likely to use the service if it offered '
     'meals, longer hours, trained caregivers, closer location, disability support or a subsidy?',
     'Removed by the study team on the final draft; not carried into this version.',
     'Study team decision. The same information is recoverable from the choice experiment.'),
    ('H1-R', 'Recommended widening of the Section H filter to include “some difficulty”.',
     'Removed by the study team on the final draft; the original filter (“a lot of difficulty” or '
     '“cannot do at all”) is retained.',
     'Study team decision.'),
    ('H2a coding', '1 = Yes, 0 = No, 98 = DK, 99 = Refused',
     'Recoded 1 = Yes, 2 = No, 3 = Don’t know, 4 = Refused, and the same code set applied '
     'throughout the instrument.',
     'Requested on the final draft: “change the coding”. Applying it once, everywhere, prevents '
     'two conventions coexisting in one dataset.'),
    ('H2e', 'Open probe listing possible support needs.',
     'Converted to a coded multi-select (H10) with the same list plus “Other”.',
     'Requested on the final draft: “tick all that applies”.'),
    ('H3 / H3a', 'Should a market childcare space take children with disabilities alongside other '
     'children? 1 = Yes together, 2 = Yes but separate room, 3 = No.  Why?',
     'Replaced by H12 and H13 (H3-R and H3a-R), which the final draft marked “retain”.',
     'The original wording frames separation as the main alternative and risks normalising '
     'exclusion, rather than asking what support the child needs to take part.'),
    ('H5', 'Confidential reporting preference.',
     'Moved to its own Section I as I1, per the final draft.',
     'Study team decision on the final draft.'),
    ('Old Section I: Close', 'Close items numbered I1–I3.',
     'Renumbered as Section J, items J1–J3.',
     'Section I is now “Concerns on childcare”; the close moves to J so that no two sections '
     'share a letter.'),
]
t = table(len(log) + 1, 4, widths=[2.4, 4.6, 4.6, 4.6])
fill_header(t, ['Draft item', 'Original wording', 'What this version does', 'Reason'], size=9)
for i, row in enumerate(log, start=1):
    _cell_text(t.rows[i].cells[0], row[0], bold=True, size=8.5)
    for j in range(1, 4):
        _cell_text(t.rows[i].cells[j], row[j], size=8.5)

# ================================================================ ANNEX B
page_break()
h1('Annex B — Old-to-new numbering map')
para('Use this map to update the ODK/CAPI form, the codebook, and any analysis syntax written '
     'against the earlier draft.', size=10, after=8)
mapping = [
    ('A1–A5', 'A1–A5', 'Unchanged; now laid out as a table.'),
    ('A6, A7', 'A6, A7', 'Unchanged; A6 recoded 1/2.'),
    ('A8-R', 'A8 + A8a', 'Adopted as the live eligibility item.'),
    ('A9', 'A9 + A9a', 'Count of flagged children added.'),
    ('—', 'A10', 'New: language of interview.'),
    ('B1', 'B1', 'Age.'),
    ('“What is your gender?”', 'B2', 'Now numbered.'),
    ('“How many year have you been selling…”', 'B3', 'Now numbered.'),
    ('B2', 'B4', 'Education.'),
    ('B3', 'B5', 'Marital status.'),
    ('B3a', 'B6', 'Childcare decision-maker.'),
    ('—', 'B7, B9', 'New: household size; children under 18.'),
    ('B4', 'B8', 'Adults 18+.'),
    ('B5', 'B10', 'Main income earner.'),
    ('B6', 'B11', 'What you sell.'),
    ('“Also employee you have in number”', 'B12', 'Now a numbered question.'),
    ('B7, B8', 'B13, B14', 'Days traded.'),
    ('B9, B10', 'B15, B16', 'Arrival and departure time.'),
    ('B11, B11a, B11b', 'B17, B17a, B17b', 'Low season.'),
    ('—', 'B18', 'New: gross daily sales (“question profit and sale”).'),
    ('B12-R', 'B19', 'Net daily earnings after all business expenses.'),
    ('B13', 'B20 + B20a', 'Income variability; best/worst day range added.'),
    ('B14, B14a, reason list, B14b', 'B21, B21a, B21b, B21c', 'Productivity loss; reason list now coded.'),
    ('B14b (second)', 'B22', 'Biggest business challenge.'),
    ('B14c-', 'B23 + B23a', 'Problems with current arrangement; main problem separated.'),
    ('B15 + “add this one”', 'B24 + B24a', 'Unmet need; number of days added.'),
    ('C1–C3 (both blocks)', 'C1, C2, C3–C6', 'Two rosters merged into one child list.'),
    ('C4', 'C7', 'Where the child is during market hours.'),
    ('C5', 'C8', 'Amount paid.'),
    ('C6', 'C9a, C9b', 'Travel time from home and from stall separated.'),
    ('C7', 'C10', 'Where the child stays at the stall.'),
    ('C8', 'C11', 'Incidents in the last 3 months.'),
    ('C8a-R', 'C11a, C11b', 'Counts per event; action taken.'),
    ('C9', 'C12', 'Child functioning (WG). Gates H6–H13.'),
    ('C10', 'C13', 'Respondent functioning (WG). Gates H1–H5.'),
    ('D1, D1a, D1b, D1c, D1d, D2', 'D1, D2, D3, D4, D5, D6', 'Sub-items promoted to full numbers.'),
    ('E1', 'E1', 'Now a rating grid; item j re-scoped to 0–3 years.'),
    ('E2', 'E2 + E2a', 'Main reason separated from the multi-select.'),
    ('E2a', 'E3 (E3a–E3d)', 'Promoted into the numbered sequence.'),
    ('E3-R', 'E4 + E4a', 'Expanded responsibility matrix.'),
    ('E4', 'E5', 'Complaint route.'),
    ('E5-R', '—', 'Removed on the final draft.'),
    ('—', 'F0, F0a–F0d', 'New: model show-card; design spec; cheap talk; reading and block rules.'),
    ('Block 1 / 2, Sets 1–6', 'F1–F6 within each block', 'Same variables; block records the card set shown.'),
    ('Enumerator notes', 'F7, F8, F8a, F9', 'Now numbered questions with codes.'),
    ('G1', 'G1', 'Now a rating grid.'),
    ('G2a', 'G2', 'Maximum daily price.'),
    ('G2b', 'G3', 'Payment authorisation (married filter retained, recoded 1–4).'),
    ('G3', 'G4', 'Payment frequency.'),
    ('G4', 'G5', 'Second child aged 0–3.'),
    ('G4-R', 'G6', 'Second child under 8 with a disability.'),
    ('G5', 'G7', 'Days per week at the stated price.'),
    ('G6', '—', 'Removed on the final draft.'),
    ('H1a–H1e', 'H1–H5', 'Sub-items promoted to full numbers.'),
    ('H2a–H2f', 'H6–H11', 'Sub-items promoted; H2a recoded; H2e now a coded multi-select.'),
    ('H3-R, H3a-R', 'H12, H13', 'Adopted as the live inclusion items.'),
    ('H4', 'H14 + H14a', 'Barriers; main barrier separated.'),
    ('H5', 'I1', 'Moved to the new Section I.'),
    ('I1, I2, I3', 'J1, J2, J3', 'Close renumbered to Section J.'),
]
t = table(len(mapping) + 1, 3, widths=[5.0, 3.6, 7.6])
fill_header(t, ['Reviewed draft', 'This version', 'Note'], size=9)
for i, row in enumerate(mapping, start=1):
    _cell_text(t.rows[i].cells[0], row[0], size=8.5)
    _cell_text(t.rows[i].cells[1], row[1], bold=True, size=8.5)
    _cell_text(t.rows[i].cells[2], row[2], size=8.5)

add_footer()
doc.save(OUT)
print('saved', OUT)
