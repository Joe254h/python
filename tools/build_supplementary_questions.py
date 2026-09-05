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
OUT = '/home/user/python/output/Supplementary_Questions_Objective_Coverage.docx'

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


def why(text):
    p = para('', before=1, after=7, indent=1.05)
    r = p.add_run('Why this is needed:  ')
    r.font.name = BODY_FONT; r.font.size = Pt(9.5); r.font.bold = True; r.font.color.rgb = STEEL
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(9.5); r2.font.italic = True; r2.font.color.rgb = GREY
    return p

# ================================================================ COVER
p = doc.add_paragraph('SUPPLEMENTARY QUESTIONS', style='Title')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Closing the remaining objective-coverage gaps in the trader questionnaire',
     size=13, bold=True, color=STEEL, after=2).alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Designing Gender-Responsive Childcare Services in Uasin Gishu County Markets  ·  '
     'Companion to Trader Questionnaire v2.0',
     size=10, italic=True, color=GREY, after=14).alignment = WD_ALIGN_PARAGRAPH.CENTER

h2('What this document is')
para('Trader Questionnaire v2.0 was audited question by question against the four study '
     'objectives and their research questions. This document contains only what the audit found '
     'missing. Every proposed question is presented under the section of v2.0 it belongs in, '
     'with a number that continues that section’s existing sequence, so items can be inserted '
     'without renumbering anything already in the instrument. Nothing here replaces an existing '
     'question.', after=6)
para('These are proposals, not corrections. Each carries the reason it was proposed so the team '
     'can accept, reword, or reject it on the merits. Adopting all of them adds roughly 24 items '
     'and an estimated 10–14 minutes to the interview; the priority column says which to keep if '
     'the instrument has to stay short.', after=8)

h2('Verdict by objective')
cov = [
    ('i', 'Feasibility and implementation readiness — infrastructure, regulatory requirements, '
          'workforce capacity',
     'Not covered by this instrument, by design',
     'This is a supply-side objective. It is answered by the KII guide, the facility audit and '
     'the literature review, not by traders. The trader questionnaire contributes only E4. '
     'See “Gaps outside the questionnaire” — the tools that carry this objective are not all '
     'written yet.'),
    ('ii', 'Demand, preferences and willingness to pay; service attributes and barriers to uptake',
     'Covered',
     'Sections C, E, F and G answer this in full. Three additions below strengthen it: payment '
     'history as an anchor for stated WTP, a norms battery the proposal promised, and the '
     'assurance package that would earn trust.'),
    ('iii', 'Barriers, accessibility needs and design requirements for inclusive childcare; how '
            'policy and operational models should be structured for inclusion and equity',
     'Mostly covered',
     'C12, C13 and H1–H14 cover the barriers and the child’s needs well. The second half of the '
     'objective — how models should be structured — is asked of county officials in the KII but '
     'never of traders. H15–H18 close that.'),
    ('iv', 'Models that balance feasibility, demand, cost, quality, sustainability and scalability',
     'Partly covered',
     'The demand and revenue sides exist (DCE, G1, G2). Two pieces are missing: the benefit side '
     '— what traders expect childcare to change about their trading — and the financing side — '
     'how the money would actually be collected, and whether a market-fee levy would be '
     'accepted. Without those, the model comparison has a cost column and no benefit column.'),
]
t = table(len(cov) + 1, 4, widths=[1.1, 5.0, 3.1, 7.0])
fill_header(t, ['Obj.', 'Objective', 'Verdict', 'Basis'], size=9)
for i, r in enumerate(cov, start=1):
    _cell_text(t.rows[i].cells[0], r[0], bold=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    _cell_text(t.rows[i].cells[1], r[1], size=8.5)
    _cell_text(t.rows[i].cells[2], r[2], bold=True, size=8.5)
    _cell_text(t.rows[i].cells[3], r[3], size=8.5)

h2('Summary of proposed additions')
summ = [
    ('B25–B28', 'Residence, travel mode, journey time, whether a child travels with you',
     'ii, iii', 'High'),
    ('C14–C15', 'Past experience of paying for childcare; hours of care needed per week',
     'ii, iv', 'High'),
    ('E6', 'Norms and perceptions battery (6 statements)', 'ii', 'High'),
    ('E7', 'What assurance would earn trust', 'ii, iv', 'Medium'),
    ('G8–G9', 'Expected change in trading days, hours, income and business decisions',
     'iv', 'High'),
    ('G10–G11', 'Preferred payment channel and willingness to pay in advance', 'iv', 'High'),
    ('G12', 'Acceptability of a market-fee levy as an alternative financing route', 'iv', 'High'),
    ('H15–H16', 'Should inclusion be mandatory for all operators; who pays for accessibility',
     'iii, iv', 'High'),
    ('H17–H18', 'NCPWD registration; who manages drop-off if the respondent cannot', 'iii',
     'Medium'),
    ('I2–I3', 'What complainants expect to happen; whether complaining feels safe', 'iii, iv',
     'Medium'),
    ('J4–J8', 'Interview timing, third-party presence, language used, interview outcome',
     'Data quality', 'High'),
]
t = table(len(summ) + 1, 4, widths=[2.3, 8.6, 2.3, 3.0])
fill_header(t, ['Proposed items', 'Content', 'Objective', 'Priority'], size=9)
for i, r in enumerate(summ, start=1):
    _cell_text(t.rows[i].cells[0], r[0], bold=True, size=8.5)
    _cell_text(t.rows[i].cells[1], r[1], size=8.5)
    _cell_text(t.rows[i].cells[2], r[2], size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    _cell_text(t.rows[i].cells[3], r[3], size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
instr('Yes/No items follow the v2.0 convention: 1 = Yes, 2 = No, 3 = Don’t know, '
      '4 = Refused. Rating scales carry their own codes, shown with each question.')

page_break()

# ================================================================ SECTION B
h1('Section B — Respondent & work')
instr('Insert after B24. Continues the existing sequence.')

h2('Catchment and journey — B25 to B28')
q('B25.', 'Where do you live? Record the estate, village or sub-location name.  '
          '____________________________')
q('B26.', 'How do you usually travel from home to this market?',
  '1 = Walk   2 = Matatu / bus   3 = Boda boda   4 = Own bicycle or motorcycle   '
  '5 = Own vehicle   6 = Handcart   7 = Other ____________')
q('B27.', 'How long does that journey take, one way?  ________ minutes')
q('B28.', 'Do you bring a child aged 0–3 with you on that journey?',
  '1 = Yes, always   2 = Sometimes   3 = No')
why('The instrument asks how far a childcare space may be from the stall (E3d) but never where '
    'the trader starts from. Without residence, travel mode and journey time you cannot say '
    'whether a market-based centre is reachable at opening time, whether a home-area centre '
    'would compete with it, or how far a mother with a disability travels before she even '
    'reaches the market. B28 also establishes how many children already make the journey daily, '
    'which is the realistic upper bound on same-day enrolment.')

page_break()

# ================================================================ SECTION C
h1('Section C — Children & current care arrangements')
instr('Insert after C13. Ask C14 of every respondent; ask C15 once per child on the roster.')

h2('Payment history — C14')
q('C14.', 'Have you ever paid anyone for childcare, at any time in the past — including a '
          'neighbour, a relative, a house help or a daycare?', YNDK)
q('C14a.', 'If C14 = 1: What is the most you ever paid?  KES ________  per  '
           '1 = Day   2 = Week   3 = Month')
q('C14b.', 'If C14 = 1 and you are not paying for childcare now: Why did that arrangement end?  '
           '(open question, then code)')
para('_' * 92, size=10, indent=1.05, after=6)
why('Stated willingness to pay in Section G is anchored by nothing if the respondent has never '
    'paid for care. Revealed payment history is the single best check on a stated WTP figure: '
    'a trader who once paid KES 100 a day and stopped is telling you something different from a '
    'trader who has never paid anything. C8 captures payment only for those currently using paid '
    'care, which excludes exactly the group whose WTP is least certain. C14b also surfaces why '
    'paid arrangements fail, which is direct evidence on sustainability.')

h2('Volume of care needed — C15')
q('C15.', 'In a normal week, how many hours in total do you need someone to care for this child '
          'while you work?  ________ hours per week')
instr('Ask once for each child on the roster. If the answer varies by season, record a normal '
      'trading week.')
why('The facility audit converts floor area into a child capacity using a space standard. '
    'Capacity in children only becomes capacity in places once you know how many hours each '
    'child needs: a centre serving 40 children for three hours is a different building, staffing '
    'roster and cost base from one serving 40 children for eleven. This is the demand-side number '
    'the audit cannot produce on its own.')

page_break()

# ================================================================ SECTION E
h1('Section E — Service attributes & barriers')
instr('Insert after E5.')

h2('E6.  Norms and perceptions')
q('E6.', 'I am going to read some things people say about childcare and about women working. '
         'For each one, tell me whether you strongly agree, agree, disagree, or strongly disagree.')
instr('Read each statement in full. Tick one box per row. Do not offer a middle option; record '
      '5 = Don’t know only if the respondent volunteers it.')
norms = [
    ('a', 'A child under three is best cared for by their own mother.'),
    ('b', 'A woman who leaves her young child at a daycare is neglecting the child.'),
    ('c', 'Men in this market would support their wives using a childcare space here.'),
    ('d', 'Other traders would think well of a mother who used a market childcare space.'),
    ('e', 'It is acceptable for a father to drop off and collect a child from childcare.'),
    ('f', 'Paying for childcare is a good use of household money.'),
    ('g', 'A woman should be able to decide on her own to enrol her child.'),
]
nscale = ['1\nStrongly agree', '2\nAgree', '3\nDisagree', '4\nStrongly disagree', '5\nDon’t know']
t = table(len(norms) + 1, 7, widths=[0.8, 5.6, 1.95, 1.95, 1.95, 1.95, 1.95])
fill_header(t, ['', 'Statement'] + nscale, size=8.5)
for i, (ltr, txt) in enumerate(norms, start=1):
    _cell_text(t.rows[i].cells[0], ltr, bold=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    _cell_text(t.rows[i].cells[1], txt, size=9)
    for j in range(2, 7):
        _cell_text(t.rows[i].cells[j], '☐', size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
why('The methodology states that the study will “examine prevailing norms and perceptions '
    'surrounding childcare and maternal employment”. At present only the focus groups touch this, '
    'so norms can be described but never related to uptake. With a short battery on 300 '
    'respondents, norms become a variable: you can test whether normative disapproval predicts '
    'opting out in the choice experiment, whether it depresses willingness to pay independently '
    'of income, and whether it differs between the men’s and women’s samples. Items c, d and e '
    'also give the county the specific belief to address in any sensitisation campaign, rather '
    'than a general finding that norms matter.')

h2('E7.  Assurance and trust')
q('E7.', 'What would you need to see before you trusted a childcare space in this market enough '
         'to leave your child there?  (tick all that apply — do not read the list)',
  '1 = Licence or permit displayed   2 = Caregivers’ certificates displayed   '
  '3 = A county inspection record I can see   4 = A parents’ committee I could join   '
  '5 = Other mothers I know already using it   6 = Being able to visit at any time without '
  'notice   7 = Visible security or controlled entry   8 = A named person who is answerable   '
  '9 = Other ____________')
q('E7a.', 'Of those, which one matters most?  ________  (enter one code from E7)')
why('E1(i) establishes that accountability matters and E5 establishes where a complaint would go, '
    'but neither says what visible evidence would actually earn a mother’s trust on day one. '
    'This is an operational specification: whichever model the county chooses has to build these '
    'signals into it, and they cost money. Item 5 is worth isolating because it means uptake will '
    'be driven by early users rather than by advertising, which changes how the centre should be '
    'launched.')

page_break()

# ================================================================ SECTION G
h1('Section G — Willingness to pay')
instr('Insert after G7. Ask in the order given, after the choice experiment.')

h2('Expected effect on trading — G8 and G9')
filt('Ask G8 and G9 only after B21 has been recorded. B21 measures what childcare problems cost '
     'the trader today; G8 measures what she expects to gain. Asking G8 first would inflate B21.')
q('G8.', 'Suppose a childcare space like the one we described were available here, at a price you '
         'could afford. In a normal week, how would your trading change?')
t = table(4, 3, widths=[5.4, 5.4, 5.4])
fill_header(t, ['', 'Direction', 'How much'], size=9)
grows = [('a.  Days you trade per week',
          '1 = More   2 = Same   3 = Fewer', 'If more: ________ extra days'),
         ('b.  Hours you trade per day',
          '1 = More   2 = Same   3 = Fewer', 'If more: ________ extra hours'),
         ('c.  Money you take home in a normal week',
          '1 = More   2 = Same   3 = Less   4 = Don’t know', 'If more: KES ________ more')]
for i, r in enumerate(grows, start=1):
    _cell_text(t.rows[i].cells[0], r[0], bold=True, size=9)
    _cell_text(t.rows[i].cells[1], r[1], size=9)
    _cell_text(t.rows[i].cells[2], r[2], size=9)
q('G9.', 'Would you make any of these changes to your business?  (tick all that apply)',
  '1 = Carry more stock   2 = Open earlier or close later   3 = Take on a helper   '
  '4 = Move to a better stall   5 = Start a second line of goods   6 = Trade on days I currently '
  'miss   7 = None of these   8 = Other ____________')
why('This is the benefit side of the comparison the fourth objective asks for. The instrument '
    'currently measures only the cost of the status quo (B21, lost trading days) and the cost of '
    'the service (Section G). A model comparison built on those two alone can rank options by '
    'affordability but cannot say whether any of them is worth building. G8 and G9 supply the '
    'return that the county has to weigh against the recurrent budget line the KII asks about. '
    'Treat stated expected gains as an upper bound and read them alongside the observed loss in '
    'B21, which is the conservative estimate — reporting both is more defensible than reporting '
    'either alone.')

h2('How the money would be collected — G10 and G11')
q('G10.', 'If you used the service, how would you prefer to pay?',
  '1 = Cash, daily   2 = M-Pesa, daily   3 = M-Pesa, weekly or monthly   '
  '4 = Added to the market fee I already pay   5 = Collected by the market committee   '
  '6 = Deducted by my sacco or group   7 = Other ____________')
q('G11.', 'Would you be willing to pay for a week or a month in advance?',
  '1 = Yes, a month in advance   2 = Yes, a week in advance   3 = No, only day by day   '
  '4 = Don’t know')
why('A willingness-to-pay figure is not revenue until there is a channel that collects it. The '
    'four models differ sharply here: a private operator needs predictable prepayment to carry '
    'staff costs, while a trader-committee model depends on daily cash collection by people who '
    'are themselves trading. E1(l) already shows that daily payment is an attribute traders care '
    'about; G10 and G11 turn that into the cash-flow assumption an operator’s budget rests on. '
    'Note also that a preference for option 4 links directly to G12.')

h2('An alternative to user fees — G12')
q('G12.', 'Some counties pay for services like this by adding a small amount to the fee that '
          'every trader in the market pays, so that childcare is free or very cheap for the '
          'parents who use it. Would you support that here?',
  '1 = Strongly support   2 = Support   3 = Oppose   4 = Strongly oppose   5 = Don’t know')
q('G12a.', 'If G12 = 1 or 2: What is the most you would accept being added to your market fee '
           'for this?  KES ________  per  1 = Day   2 = Week   3 = Month')
q('G12b.', 'If G12 = 3 or 4: What is your main reason for opposing it?  (open question, then code)')
para('_' * 92, size=10, indent=1.05, after=6)
why('User fees are the only financing route the toolkit currently tests, and the traders most '
    'likely to need childcare are the least able to pay them — so a design that balances '
    'feasibility, demand and sustainability may be unreachable through fees alone. A levy spread '
    'across all traders is the most realistic alternative in a county market, and it is the one '
    'the county can act on without new national funding. Asking non-users whether they would '
    'accept it is also the only way to find out whether the model is politically survivable: it '
    'is the men’s and the childless traders’ answers that decide that, and both groups are in '
    'the sample. G12b gives the county the objection it would have to answer.')

page_break()

# ================================================================ SECTION H
h1('Section H — Inclusion')
instr('Insert after H14a. Ask H15 and H16 of every respondent; H17 and H18 only where the filter '
      'applies.')

h2('How inclusion should be structured — H15 and H16')
q('H15.', 'Should every childcare space in county markets be required to accept children with '
          'disabilities, whoever runs it?',
  '1 = Yes, all of them   2 = Only county-run ones   3 = Only where it is practical   '
  '4 = No   5 = Don’t know')
q('H15a.', 'What is the main reason for your answer?  (open question, then code)')
para('_' * 92, size=10, indent=1.05, after=6)
q('H16.', 'Making a childcare space accessible — a ramp, an accessible toilet, a caregiver '
          'trained to support children with disabilities — costs more to build and more to run. '
          'Who should pay for that?',
  '1 = County government   2 = All parents share it in the fee   3 = Only the parents of '
  'children with disabilities   4 = National government   5 = A donor or NGO   '
  '6 = Whoever operates the space   7 = Don’t know')
q('H16a.', 'Would you be willing to pay slightly more per day so that the space is accessible to '
           'all children?',
  '1 = Yes — how much more per day? KES ________   2 = No   3 = Don’t know')
why('The third objective asks how policies and operational models can be structured to prioritise '
    'inclusion and equity. The KII asks county officials whether all four modalities should be '
    'held to the same accessibility standard; nobody asks the traders, whose answer determines '
    'whether such a rule would be accepted or quietly evaded. H16 and H16a matter more than they '
    'look: the accessibility retrofit is a real cost line in the facility audit and in the '
    'costing tool, and under a private or partnership model somebody has to carry it. If parents '
    'will not cross-subsidise it, an inclusive service is only viable where the county funds the '
    'difference — which is a finding the Market Development Policy needs stated plainly.')

h2('Registration and drop-off support — H17 and H18')
filt('Ask H17 if C12 or C13 records any difficulty. Ask H18 only if C13 records difficulty for '
     'the respondent.')
q('H17.', 'Are you, or is your child, registered with the National Council for Persons with '
          'Disabilities?',
  '1 = Yes, the respondent   2 = Yes, the child   3 = Both   4 = Neither   5 = Don’t know')
q('H17a.', 'If 4 or 5: Have you ever tried to register?', YNDK)
why('Registration is the gateway to NCPWD entitlements and is the practical test of whether '
    'documentation is a barrier — H14 lists documentation as a possible barrier but nothing '
    'establishes how many households actually hold the papers. It also connects this sample '
    'directly to the NCPWD key informant interview, so the two instruments can be read against '
    'each other rather than in parallel.')
q('H18.', 'If you could not manage the drop-off or collection yourself on a given day, who would '
          'do it?',
  '1 = Spouse or partner   2 = Another adult in the household   3 = Another trader   '
  '4 = A paid helper   5 = No one — the child would stay with me   6 = Other ____________')
why('H3 asks what the respondent would need in order to manage drop-off herself, which assumes '
    'she can. H18 covers the days she cannot. If the common answer is code 5, then physical '
    'accessibility alone will not produce attendance, and the centre needs a policy on who else '
    'may collect a child — a safeguarding rule that has to be written before the space opens.')

page_break()

# ================================================================ SECTION I
h1('Section I — Concerns on childcare')
instr('Insert after I1.')
q('I2.', 'If you made a complaint about the childcare service, what would you expect to happen?  '
         '(open question, then code)')
para('_' * 92, size=10, indent=1.05, after=2)
para('_' * 92, size=10, indent=1.05, after=6)
q('I3.', 'Would you feel safe making a complaint about a caregiver while your child was still '
         'attending?', YNDK)
q('I3a.', 'If I3 = 2: What would you do instead?',
  '1 = Withdraw the child quietly   2 = Say nothing and continue   3 = Ask someone else to '
  'raise it   4 = Raise it with other parents first   5 = Other ____________')
why('E4 assigns responsibility for receiving complaints and I1 establishes the preferred channel, '
    'but an accountability mechanism only works if people believe using it is safe. If the common '
    'answer to I3a is code 1, the centre will lose children without ever recording a complaint, '
    'and the county will read falling attendance as weak demand rather than as a quality failure. '
    'This is a small addition that protects the interpretation of every other governance finding '
    'in the study.')

page_break()

# ================================================================ SECTION J
h1('Section J — Close')
instr('Insert after J3. J4 to J8 are completed by the enumerator, not read aloud.')
q('J4.', 'Interview start time  ________ : ________     am / pm')
q('J5.', 'Interview end time  ________ : ________     am / pm')
q('J6.', 'Was anyone else present for any part of the interview?',
  '1 = No one   2 = Spouse or partner   3 = Another family member   4 = Another trader   '
  '5 = Children only   6 = Other ____________')
q('J6a.', 'If anyone other than children was present: In your judgement, did their presence '
          'appear to affect the respondent’s answers?', YNDK)
q('J7.', 'Language actually used for most of the interview',
  '1 = Kiswahili   2 = English   3 = Kalenjin   4 = Luhya   5 = Kikuyu   6 = Luo   '
  '7 = Other ____________     (compare with A10)')
q('J8.', 'Interview outcome',
  '1 = Complete   2 = Partial — respondent stopped   3 = Refused after consent   '
  '4 = Screened out at A8/A9   5 = Interrupted, to be revisited')
why('G3 asks whether a spouse must authorise the payment, E6 asks about norms, and H4 asks about '
    'being treated badly — these are precisely the items a listening spouse or fellow trader '
    'distorts. Without J6 you cannot test for that effect or control for it, and a reviewer will '
    'ask. J4 and J5 give the real interview length, which the consent script promises and which '
    'determines whether the instrument is deliverable at 300 respondents. J8 lets you build the '
    'response-rate table that any published write-up will need.')

page_break()

# ================================================================ ANNEX
h1('Gaps outside the questionnaire')
para('The audit also identified gaps that no addition to the trader questionnaire can close, '
     'because they belong to other instruments in the toolkit. They are recorded here so the '
     'decision to address them, or not, is a deliberate one.', size=10, after=8)
gaps = [
    ('The costing tool referred to as “T5”',
     'The facility audit (section 8) and the KII guide (section 7) both cross-reference a tool '
     '“T5” carrying an inclusive add-on cost line. That tool is not in the set.',
     'Objective iv cannot be answered without it. Cost and scalability are two of the four '
     'dimensions on which the models are to be compared, and no instrument currently collects '
     'unit costs, staffing costs, or the accessibility retrofit cost from providers or the '
     'county.'),
    ('Key informant guides for six of the seven respondent types',
     'The methodology plans 20 KIIs with county officials, market associations, existing and '
     'potential childcare providers, women leaders, NCPWD, NGOs and private sector actors. Only '
     'the county and regulatory guide exists.',
     'A provider cannot answer questions written for a county licensing department, and only a '
     'provider can supply the operating costs, staffing ratios and enrolment economics that '
     'objectives i and iv depend on.'),
    ('The observation guide',
     'The methodology lists five instrument types — questionnaire, FGD, KII, observation guide '
     'and facility assessment. Four exist.',
     'If the facility audit is intended to serve as the observation guide, say so in the '
     'methodology; if not, the guide is needed for the market-level observation of how children '
     'are currently kept at stalls, which is the visual evidence behind the problem statement.'),
    ('Six markets or seven',
     'The methodology specifies a survey across 6 markets. The FGD guide and the facility audit '
     'both list seven named markets. The methodology also refers to “42 operational county '
     'markets”, which reads as a national rather than a county figure.',
     'The sampling frame and the per-market sample size both depend on this. At 300 respondents '
     'it is 50 per market across six, or 43 across seven.'),
    ('Quota for men within the 300',
     'The problem statement concerns women traders; the survey is described as covering 300 '
     'women and men, and FGD Group 2 is men. No split is specified.',
     'The men’s subsample carries the norms and household-authorisation findings (E6, G3) and '
     'the levy question (G12). If it is too small to analyse separately, those findings cannot '
     'be reported by sex, which is the point of a gender-responsive design.'),
    ('Choice-card levels that fall below minimum standards',
     'The pilot cards retain “1 untrained helper per 10 children” and “no special accommodation '
     'for children with disabilities”. The design note (F0a) says to use only levels meeting '
     'minimum legal, safety and accessibility requirements.',
     'These are compatible only if those levels are lawful. Confirm the enforced minimum '
     'standards through the county KII (section 1), then drop the levels that fall below them '
     'when the design is regenerated after the pilot.'),
]
t = table(len(gaps) + 1, 3, widths=[3.6, 6.3, 6.3])
fill_header(t, ['Gap', 'What is missing', 'Why it matters'], size=9)
for i, r in enumerate(gaps, start=1):
    _cell_text(t.rows[i].cells[0], r[0], bold=True, size=8.5)
    _cell_text(t.rows[i].cells[1], r[1], size=8.5)
    _cell_text(t.rows[i].cells[2], r[2], size=8.5)

add_footer()
doc.save(OUT)
print('saved', OUT)
