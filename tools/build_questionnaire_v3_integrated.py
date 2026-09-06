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
OUT = '/home/user/python/output/Trader_Questionnaire_Integrated_v3.docx'

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


# ---- red-marked supplementary helpers ------------------------------------
def qr(num, text, codes=None):
    """Supplementary question — printed in red."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(1.05)
    p.paragraph_format.first_line_indent = Cm(-1.05)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(num + '  ')
    r.font.name = BODY_FONT; r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = RED
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(11); r2.font.color.rgb = RED
    if codes:
        c = doc.add_paragraph()
        c.paragraph_format.space_before = Pt(0); c.paragraph_format.space_after = Pt(3)
        c.paragraph_format.left_indent = Cm(1.05)
        rc = c.add_run(codes)
        rc.font.name = BODY_FONT; rc.font.size = Pt(10.5); rc.font.color.rgb = RED
    return p

def instr_r(text):
    return para(text, size=10, italic=True, color=RED, before=2, after=4, indent=1.05)

def filt_r(text):
    return para(text, size=10, bold=True, italic=True, color=RED,
                before=3, after=4, indent=1.05)

def h2r(text):
    p = doc.add_paragraph(text, style='Heading 2')
    for r in p.runs:
        r.font.color.rgb = RED
    return p

def linesr(n=1):
    for _ in range(n):
        para('_' * 92, size=10, indent=1.05, after=2, color=RED)

def new_block(title):
    """Red banner introducing the supplementary items appended to a section."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement('w:pBdr'); tp = OxmlElement('w:top')
    tp.set(qn('w:val'), 'single'); tp.set(qn('w:sz'), '6')
    tp.set(qn('w:space'), '4'); tp.set(qn('w:color'), 'C00000')
    b.append(tp); pPr.append(b)
    r = p.add_run(title)
    r.font.name = BODY_FONT; r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = RED
    return p



# ---- supplementary blocks, printed in red --------------------------------
def fill_header_r(t, labels, size=9):
    for i, lab in enumerate(labels):
        _cell_text(t.rows[0].cells[i], lab, bold=True, size=size,
                   align=WD_ALIGN_PARAGRAPH.CENTER, color=RED)
        _shade(t.rows[0].cells[i], 'FBE4E4')
    _repeat_header(t.rows[0])

def supp_B():
    new_block('Additional questions — catchment and journey')
    instr_r('Added to Section B. Ask after B24.')
    qr('B25.', 'Where do you live? Record the estate, village or sub-location name.  '
               '____________________________')
    qr('B26.', 'How do you usually travel from home to this market?',
       '1 = Walk   2 = Matatu / bus   3 = Boda boda   4 = Own bicycle or motorcycle   '
       '5 = Own vehicle   6 = Handcart   7 = Other ____________')
    qr('B27.', 'How long does that journey take, one way?  ________ minutes')
    qr('B28.', 'Do you bring a child aged 0–3 with you on that journey?',
       '1 = Yes, always   2 = Sometimes   3 = No')

def supp_C():
    new_block('Additional questions — payment history and volume of care needed')
    instr_r('Added to Section C. Ask C14 of every respondent; ask C15 once for each child on '
            'the roster.')
    qr('C14.', 'Have you ever paid anyone for childcare, at any time in the past — including a '
               'neighbour, a relative, a house help or a daycare?', YNDK)
    qr('C14a.', 'If C14 = 1: What is the most you ever paid?  KES ________  per  '
                '1 = Day   2 = Week   3 = Month')
    qr('C14b.', 'If C14 = 1 and you are not paying for childcare now: Why did that arrangement '
                'end?  (open question, then code)')
    linesr(1)
    qr('C15.', 'In a normal week, how many hours in total do you need someone to care for this '
               'child while you work?  ________ hours per week')
    instr_r('Ask once for each child on the roster. If it varies by season, record a normal '
            'trading week.')

def supp_E():
    new_block('Additional questions — norms, perceptions and trust')
    instr_r('Added to Section E. Ask after E5.')
    qr('E6.', 'I am going to read some things people say about childcare and about women '
              'working. For each one, tell me whether you strongly agree, agree, disagree, or '
              'strongly disagree.')
    instr_r('Read each statement in full. Tick one box per row. Do not offer a middle option; '
            'record 5 = Don’t know only if the respondent volunteers it.')
    norms = [
        ('a', 'A child under three is best cared for by their own mother.'),
        ('b', 'A woman who leaves her young child at a daycare is neglecting the child.'),
        ('c', 'Men in this market would support their wives using a childcare space here.'),
        ('d', 'Other traders would think well of a mother who used a market childcare space.'),
        ('e', 'It is acceptable for a father to drop off and collect a child from childcare.'),
        ('f', 'Paying for childcare is a good use of household money.'),
        ('g', 'A woman should be able to decide on her own to enrol her child.'),
    ]
    nscale = ['1\nStrongly agree', '2\nAgree', '3\nDisagree', '4\nStrongly disagree',
              '5\nDon’t know']
    t = table(len(norms) + 1, 7, widths=[0.8, 5.6, 1.95, 1.95, 1.95, 1.95, 1.95])
    fill_header_r(t, ['', 'Statement'] + nscale, size=8.5)
    for i, (ltr, txt) in enumerate(norms, start=1):
        _cell_text(t.rows[i].cells[0], ltr, bold=True, size=9,
                   align=WD_ALIGN_PARAGRAPH.CENTER, color=RED)
        _cell_text(t.rows[i].cells[1], txt, size=9, color=RED)
        for j in range(2, 7):
            _cell_text(t.rows[i].cells[j], '☐', size=10,
                       align=WD_ALIGN_PARAGRAPH.CENTER, color=RED)
    qr('E7.', 'What would you need to see before you trusted a childcare space in this market '
              'enough to leave your child there?  (tick all that apply — do not read the list)',
       '1 = Licence or permit displayed   2 = Caregivers’ certificates displayed   '
       '3 = A county inspection record I can see   4 = A parents’ committee I could join   '
       '5 = Other mothers I know already using it   6 = Being able to visit at any time without '
       'notice   7 = Visible security or controlled entry   8 = A named person who is answerable '
       '  9 = Other ____________')
    qr('E7a.', 'Of those, which one matters most?  ________  (enter one code from E7)')

def supp_G():
    new_block('Additional questions — expected effect, collection and financing')
    instr_r('Added to Section G. Ask after G7, in the order given.')
    filt_r('Ask G8 and G9 only after B21 has been recorded. B21 measures what childcare problems '
           'cost the trader today; G8 measures what she expects to gain. Asking G8 first would '
           'inflate B21.')
    qr('G8.', 'Suppose a childcare space like the one we described were available here, at a '
              'price you could afford. In a normal week, how would your trading change?')
    grows = [('a.  Days you trade per week', '1 = More   2 = Same   3 = Fewer',
              'If more: ________ extra days'),
             ('b.  Hours you trade per day', '1 = More   2 = Same   3 = Fewer',
              'If more: ________ extra hours'),
             ('c.  Money you take home in a normal week',
              '1 = More   2 = Same   3 = Less   4 = Don’t know', 'If more: KES ________ more')]
    t = table(4, 3, widths=[5.4, 5.4, 5.4])
    fill_header_r(t, ['', 'Direction', 'How much'], size=9)
    for i, r in enumerate(grows, start=1):
        _cell_text(t.rows[i].cells[0], r[0], bold=True, size=9, color=RED)
        _cell_text(t.rows[i].cells[1], r[1], size=9, color=RED)
        _cell_text(t.rows[i].cells[2], r[2], size=9, color=RED)
    qr('G9.', 'Would you make any of these changes to your business?  (tick all that apply)',
       '1 = Carry more stock   2 = Open earlier or close later   3 = Take on a helper   '
       '4 = Move to a better stall   5 = Start a second line of goods   6 = Trade on days I '
       'currently miss   7 = None of these   8 = Other ____________')
    qr('G10.', 'If you used the service, how would you prefer to pay?',
       '1 = Cash, daily   2 = M-Pesa, daily   3 = M-Pesa, weekly or monthly   '
       '4 = Added to the market fee I already pay   5 = Collected by the market committee   '
       '6 = Deducted by my sacco or group   7 = Other ____________')
    qr('G11.', 'Would you be willing to pay for a week or a month in advance?',
       '1 = Yes, a month in advance   2 = Yes, a week in advance   3 = No, only day by day   '
       '4 = Don’t know')
    qr('G12.', 'Some counties pay for services like this by adding a small amount to the fee '
               'that every trader in the market pays, so that childcare is free or very cheap '
               'for the parents who use it. Would you support that here?',
       '1 = Strongly support   2 = Support   3 = Oppose   4 = Strongly oppose   5 = Don’t know')
    qr('G12a.', 'If G12 = 1 or 2: What is the most you would accept being added to your market '
                'fee for this?  KES ________  per  1 = Day   2 = Week   3 = Month')
    qr('G12b.', 'If G12 = 3 or 4: What is your main reason for opposing it?  '
                '(open question, then code)')
    linesr(1)

def supp_H():
    new_block('Additional questions — how inclusion should be structured')
    instr_r('Added to Section H. Ask H15 and H16 of every respondent; H17 and H18 only where the '
            'filter applies.')
    qr('H15.', 'Should every childcare space in county markets be required to accept children '
               'with disabilities, whoever runs it?',
       '1 = Yes, all of them   2 = Only county-run ones   3 = Only where it is practical   '
       '4 = No   5 = Don’t know')
    qr('H15a.', 'What is the main reason for your answer?  (open question, then code)')
    linesr(1)
    qr('H16.', 'Making a childcare space accessible — a ramp, an accessible toilet, a caregiver '
               'trained to support children with disabilities — costs more to build and more to '
               'run. Who should pay for that?',
       '1 = County government   2 = All parents share it in the fee   3 = Only the parents of '
       'children with disabilities   4 = National government   5 = A donor or NGO   '
       '6 = Whoever operates the space   7 = Don’t know')
    qr('H16a.', 'Would you be willing to pay slightly more per day so that the space is '
                'accessible to all children?',
       '1 = Yes — how much more per day? KES ________   2 = No   3 = Don’t know')
    filt_r('Ask H17 if C12 or C13 records any difficulty. Ask H18 only if C13 records difficulty '
           'for the respondent.')
    qr('H17.', 'Are you, or is your child, registered with the National Council for Persons with '
               'Disabilities?',
       '1 = Yes, the respondent   2 = Yes, the child   3 = Both   4 = Neither   5 = Don’t know')
    qr('H17a.', 'If 4 or 5: Have you ever tried to register?', YNDK)
    qr('H18.', 'If you could not manage the drop-off or collection yourself on a given day, who '
               'would do it?',
       '1 = Spouse or partner   2 = Another adult in the household   3 = Another trader   '
       '4 = A paid helper   5 = No one — the child would stay with me   6 = Other ____________')

def supp_I():
    new_block('Additional questions — whether the complaint route works')
    instr_r('Added to Section I. Ask after I1.')
    qr('I2.', 'If you made a complaint about the childcare service, what would you expect to '
              'happen?  (open question, then code)')
    linesr(1)
    qr('I3.', 'Would you feel safe making a complaint about a caregiver while your child was '
              'still attending?', YNDK)
    qr('I3a.', 'If I3 = 2: What would you do instead?',
       '1 = Withdraw the child quietly   2 = Say nothing and continue   3 = Ask someone else to '
       'raise it   4 = Raise it with other parents first   5 = Other ____________')

def supp_J():
    new_block('Additional items — fieldwork record')
    instr_r('Added to Section J. Completed by the enumerator, not read aloud.')
    qr('J4.', 'Interview start time  ________ : ________     am / pm')
    qr('J5.', 'Interview end time  ________ : ________     am / pm')
    qr('J6.', 'Was anyone else present for any part of the interview?',
       '1 = No one   2 = Spouse or partner   3 = Another family member   4 = Another trader   '
       '5 = Children only   6 = Other ____________')
    qr('J6a.', 'If anyone other than children was present: In your judgement, did their presence '
               'appear to affect the respondent’s answers?', YNDK)
    qr('J7.', 'Language actually used for most of the interview',
       '1 = Kiswahili   2 = English   3 = Kalenjin   4 = Luhya   5 = Kikuyu   6 = Luo   '
       '7 = Other ____________     (compare with A10)')
    qr('J8.', 'Interview outcome',
       '1 = Complete   2 = Partial — respondent stopped   3 = Refused after consent   '
       '4 = Screened out at A8/A9   5 = Interrupted, to be revisited')



# ================================================================ OPENING
# Reproduced verbatim from the reviewed draft (paragraphs 0-25), except the
# review key, which is replaced by a key describing this document's own marking.
OPEN = Document(
    '/root/.claude/uploads/920ad5d8-6e07-5909-9e17-40c3ac0fe128/'
    '5186effd-Joel_Questionnaire_Objective_Aligned_Reviewed.docx').paragraphs

def src_text(i):
    return OPEN[i].text.strip()

p = para(src_text(0), size=18, bold=True, color=NAVY, after=4)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p = para(src_text(1), size=12.5, bold=True, color=STEEL, after=12)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

# --- key describing this document ---
para('KEY', size=11, bold=True, color=NAVY, before=2, after=3)
p = para('', after=2)
r = p.add_run('Red text: ')
r.font.name = BODY_FONT; r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = RED
r2 = p.add_run('a supplementary question added to close a gap in objective coverage. '
               'Red items are new; everything in black is carried over from the reviewed draft.')
r2.font.name = BODY_FONT; r2.font.size = Pt(10.5); r2.font.color.rgb = RED
para('Black text: the questionnaire as reviewed and resolved — every recommendation adopted, '
     'numbered sequentially within its section.', size=10.5, after=2)
para('Coding: Yes/No items use 1 = Yes, 2 = No, 3 = Don’t know, 4 = Refused throughout. Rating '
     'scales carry their own codes, shown with the question.', size=10.5, after=10)

h1('Participant consent form')
instr(src_text(6))
para(src_text(7), after=6)
para(src_text(8), after=6)
para(src_text(10), after=2)
para(src_text(11), after=8)
para(src_text(12), bold=True, after=8)
para(src_text(13), size=10.5, after=6)
for i in (14, 15, 16):
    para(src_text(i), size=10.5, after=4)
para(src_text(17), size=10.5, bold=True, before=6, after=4)
for i in (18, 19):
    para(src_text(i), size=10.5, after=4)
para(src_text(20), size=10.5, bold=True, before=6, after=4)
for i in (21, 22, 23):
    para(src_text(i), size=10.5, after=4)
para(src_text(24), size=10.5, before=6, after=2)
instr(src_text(25))

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
instr('Replaces the original A8 (“Do you have any child aged 0–3 currently in your care?”). '
      'This fixes the principal childcare population at ages 0–3 and links eligibility directly '
      'to care responsibilities on market days.')

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
instr('Replaces the original B12, which asked only what remained after paying for stock. '
      'Netting out transport, market fees and helpers gives a clearer affordability measure.')
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


supp_B()

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


supp_C()

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


supp_E()

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


supp_G()

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

supp_H()

page_break()

# ================================================================ SECTION I
h1('Section I — Concerns on childcare')
q('I1.', 'If you had a concern about the childcare service, how would you prefer to report it '
         'confidentially?',
  '1 = In person   2 = Telephone   3 = SMS / WhatsApp   4 = Suggestion or complaint box   '
  '5 = Through a representative or organisation   6 = Other ____________')

supp_I()

page_break()

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

supp_J()

add_footer()
doc.save(OUT)
print('saved', OUT)