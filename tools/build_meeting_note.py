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
OUT = '/home/user/python/output/Client_Meeting_Discussion_Note.docx'

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


def kv(label, text, size=10.5):
    p = para('', before=2, after=3, indent=1.05)
    r = p.add_run(label + '  ')
    r.font.name = BODY_FONT; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = STEEL
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(size)
    return p

def body(text, size=11, after=6):
    return para(text, size=size, after=after)

def rec(text):
    """Recommendation callout."""
    p = para('', before=6, after=8)
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement('w:pBdr')
    for side in ('left',):
        e = OxmlElement('w:' + side)
        e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '18')
        e.set(qn('w:space'), '8'); e.set(qn('w:color'), '1F4D78')
        b.append(e)
    pPr.append(b)
    p.paragraph_format.left_indent = Cm(0.5)
    r = p.add_run('Our recommendation:  ')
    r.font.name = BODY_FONT; r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = STEEL
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(10.5)
    return p

def flag(text):
    p = para('', before=6, after=8)
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement('w:pBdr')
    e = OxmlElement('w:left')
    e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '18')
    e.set(qn('w:space'), '8'); e.set(qn('w:color'), 'C00000')
    b.append(e); pPr.append(b)
    p.paragraph_format.left_indent = Cm(0.5)
    r = p.add_run('Must be settled first:  ')
    r.font.name = BODY_FONT; r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = RED
    r2 = p.add_run(text)
    r2.font.name = BODY_FONT; r2.font.size = Pt(10.5)
    return p

def tbl(header, rows, widths, size=9, hdrsize=9):
    t = table(len(rows) + 1, len(header), widths=widths)
    fill_header(t, header, size=hdrsize)
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            _cell_text(t.rows[ri].cells[ci], val, bold=(ci == 0), size=size)
    return t

# ================================================================ COVER
p = doc.add_paragraph('DISCUSSION NOTE', style='Title')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Three items to settle before fieldwork: the choice experiment, a wellbeing measure, '
     'and costing', size=12.5, bold=True, color=STEEL, after=2).alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Designing Gender-Responsive Childcare Services in Uasin Gishu County Markets  ·  '
     'Prepared for the client meeting', size=10, italic=True, color=GREY,
     after=14).alignment = WD_ALIGN_PARAGRAPH.CENTER

h2('Purpose')
body('Three things came up that need a decision before the survey goes to the field. Two of them '
     '— the choice experiment and the costing template — block work that is already scheduled. '
     'The third, adding a wellbeing measure, is an addition worth making but it carries an '
     'obligation we should agree on openly before we commit to it.')
body('This note sets out where each stands, what we think should happen, and what we need '
     'decided in the meeting. Each section ends with the specific decision required.')

h2('At a glance')
tbl(['Item', 'Status', 'What the meeting must produce', 'Blocks'],
    [['1. Choice experiment', 'Drafted; pilot design only',
      'Sign-off on the seven attributes and their levels, and agreement on the pilot-then-'
      'regenerate sequence',
      'Printing of show-cards; main survey'],
     ['2. Wellbeing measure', 'Not yet in the instrument',
      'Choice of measure, agreement on why we are measuring it, and a referral pathway',
      'Ethics submission; questionnaire sign-off'],
     ['3. Costing template', 'Drafted as Section K; no data source for half of it',
      'Agreement to run provider interviews, and who supplies county cost figures',
      'Any statement about which model is sustainable']],
    widths=[3.4, 3.6, 6.4, 3.2])

page_break()

# ================================================================ ITEM 1
h1('1.  The discrete choice experiment')

h2('Where it stands')
body('The experiment is built and the cards are drafted. What exists is a pilot design: it uses '
     'assumed values for how much traders care about each feature, because we have no data yet '
     'from which to estimate them. That is the normal way to start, but it means the current '
     'cards are not the cards we run the main survey on.')
body('Four things are unresolved, and three of them cannot be closed in the meeting alone — they '
     'depend on answers from the County. That sequencing is the main thing to agree.')

h2('1.1  How many features, and which')
body('The design note says six features; the cards actually carry seven. The seven are cost, '
     'location, opening hours, caregiver ratio and training, food, who runs it, and inclusion. '
     'We think seven is right — dropping one would mean dropping something the County has to '
     'decide about anyway — but it needs to be stated once and consistently.')
rec('Confirm seven attributes. Correct the design note to match the cards rather than the other '
    'way round.')

h2('1.2  Some of the current levels may not be lawful')
body('Two levels on the cards describe care that may fall below the minimum standard the County '
     'enforces: "one untrained helper per ten children", and "no special accommodation for '
     'children with disabilities". If those arrangements would not be licensed, we should not be '
     'asking traders to trade them off against price, because no one could legally offer them. '
     'Keeping them would produce a willingness-to-pay figure for a service that cannot exist.')
flag('We cannot settle this in the meeting. It depends on what minimum standards the County '
     'actually enforces — ratios, caregiver qualifications, and whether accessibility is '
     'mandatory. That is section 1 of the county interview guide. The choice experiment cannot '
     'be finalised until that interview has happened.')
rec('Run the county regulatory interview first. Then drop any level that falls below the '
     'enforced minimum, and regenerate the design.')

h2('1.3  The price range')
body('The cards currently test KES 30, 60, 100 and 150 per day. If the true acceptable price '
     'sits outside that range, the estimate will be anchored to the range rather than measured. '
     'Two checks will tell us: what traders report earning after costs, and what existing '
     'daycares in and around these markets actually charge.')
rec('Check the range against provider fees and trader earnings before printing. Widen or narrow '
    'it once, on the basis of those two figures, and then leave it alone.')

h2('1.4  Balance across the cards')
body('In the current draft the trader-committee option appears on only two of the twelve cards, '
     'and a few cards hold price constant across both options. That weakens our ability to '
     'estimate how traders value that model and how they respond to price. It is a technical '
     'fault in the draft design, not a judgement call, and it is fixed by regenerating the '
     'design rather than by editing cards by hand.')

h2('1.5  The sequence we propose')
tbl(['Step', 'What happens', 'Why it has to be in this order'],
    [['1', 'County regulatory interview',
      'Tells us which levels are lawful, and the enforced ratio and space standard'],
     ['2', 'Provider interviews and a check on current fees',
      'Tells us whether the price range is realistic'],
     ['3', 'Finalise attributes and levels; regenerate the design',
      'The design can only be built once the levels are fixed'],
     ['4', 'Pilot with 30 respondents',
      'Tests whether traders can read the cards and gives us real values to work from'],
     ['5', 'Re-estimate and regenerate the final design; print show-cards',
      'This is the version the 300 respondents see'],
     ['6', 'Main survey', '']],
    widths=[1.3, 6.8, 8.5])
body('Steps 4 and 5 are the ones most often skipped under time pressure. We would rather flag '
     'now that skipping them means reporting preferences estimated from assumed values, and '
     'saying so in the write-up.', after=4)

h2('1.6  Two smaller points to confirm')
bullet('The "I would use neither" option stays on every card. It is what tells us how many '
       'traders would not use a market service at any of these prices — which is as much a '
       'finding as any preference ranking.', size=10.5)
bullet('Show-cards need pictures, not just text, because some respondents will not read '
       'comfortably. Icons have to be drawn and printed, and that has a lead time worth putting '
       'in the schedule now.', size=10.5)

h2('Decision required')
tbl(['#', 'Decision', 'Who decides'],
    [['1.1', 'Seven attributes confirmed', 'Study team and client'],
     ['1.2', 'Levels below the enforced minimum will be dropped once the County confirms them',
      'Client, on our recommendation'],
     ['1.3', 'Price range to be checked against provider fees before printing', 'Study team'],
     ['1.4', 'Design to be regenerated rather than hand-edited', 'Study team'],
     ['1.5', 'Pilot of 30 and a second design round are accepted in the timeline',
      'Client — this is the one with schedule consequences']],
    widths=[1.2, 10.4, 5.0])

page_break()

# ================================================================ ITEM 2
h1('2.  Adding a wellbeing measure')

h2('Why it is worth adding')
body('The study currently measures what childcare costs a trader in money and lost trading days. '
     'It does not measure what it costs her otherwise. Caring for a young child at a market stall '
     'while trying to trade is a plausible source of sustained strain, and if we intend to argue '
     'that childcare is worth the County\'s money, wellbeing is part of the return — alongside '
     'the trading days recovered.')
body('It also works the other way. A trader under heavy strain may behave differently in the '
     'choice experiment and in what she says she would pay. Measuring it lets us check that '
     'rather than assume it away.')

h2('2.1  Be clear which of two purposes we are serving')
body('These need different things from us, so it is worth settling explicitly:')
bullet('As a baseline. We measure now, expecting a later round to measure again once a service '
       'is running. This is the stronger use, but it only works if a follow-up is actually '
       'planned and funded.', size=10.5)
bullet('As an explanatory variable. We use it to understand who takes up childcare and who does '
       'not. This works with the single round we have, but it can only show association — never '
       'that childcare improved anyone\'s wellbeing.', size=10.5)
flag('If we have one round only, we must not write it up as though childcare caused a change in '
     'wellbeing. Agreeing this now avoids a claim in the report that the design cannot support.')

h2('2.2  Which measure')
body('Four short, established options. All are free to use and all have been used widely in '
     'low- and middle-income settings. The team should confirm the current scoring thresholds '
     'and obtain an existing validated Kiswahili translation rather than translating afresh.')
tbl(['Measure', 'Items', 'What it captures', 'Fit for this study'],
    [['WHO-5 Well-Being Index', '5',
      'General wellbeing over the past two weeks. Positively worded throughout.',
      'Best fit. About one minute. Nothing in it sounds like a diagnosis, which matters when '
      'we are interviewing at a stall with other traders nearby.'],
     ['PHQ-2, or PHQ-9 in full', '2 or 9',
      'Low mood and loss of interest; the nine-item version screens for depression.',
      'Use only if the client wants clinical screening. It asks directly about mood and '
      'hopelessness, which raises the duty of care considerably.'],
     ['GAD-2, or GAD-7', '2 or 7', 'Anxiety and worry.',
      'Worth pairing with PHQ-2 if screening is wanted; four items in total.'],
     ['Kessler K6', '6', 'General psychological distress.',
      'A reasonable alternative to WHO-5 where distress rather than wellbeing is the focus.']],
    widths=[3.4, 1.4, 5.2, 6.6])
rec('WHO-5. Five items, roughly one minute, positively worded, and it answers both purposes '
    'above. If the client specifically wants a screening instrument rather than a wellbeing '
    'measure, add PHQ-2 and GAD-2 — four items — but only with the referral pathway in 2.3 '
    'agreed first.')

h2('2.3  The obligation this creates')
body('Asking these questions means some respondents will disclose real distress. Once we have '
     'asked, we cannot simply record the answer and move on.')
tbl(['What is needed', 'Detail'],
    [['A referral pathway', 'Agreed in writing with the County health department before '
      'fieldwork: where a trader who needs support is sent, and whether that service is free '
      'and reachable from the market.'],
     ['Enumerator training', 'What to do when a respondent becomes distressed: pause, do not '
      'probe, offer the referral, and record nothing beyond the answers.'],
     ['A referral card', 'A physical card with contact details, given to anyone who scores '
      'above the threshold or who asks for it — handed out without comment or singling out.'],
     ['Ethics approval', 'The submission has to say we are collecting mental health data, how '
      'we store it, and what our referral protocol is. This is a substantive amendment, not a '
      'wording change.'],
     ['Consent wording', 'The consent script must mention that some questions ask how the '
      'respondent has been feeling, and that these can be skipped.']],
    widths=[4.2, 12.4])
flag('The ethics amendment is the item with the longest lead time. If we are adding this, the '
     'submission should be prepared in parallel with finalising the choice experiment, not '
     'after it.')

h2('2.4  Where it goes in the questionnaire')
body('At the end, after willingness to pay and after the choice experiment, immediately before '
     'the closing questions. It must not come before the question on trading days lost to '
     'childcare, and it must not come before the choice cards — asking someone to reflect on how '
     'they have been feeling and then asking what they would pay is likely to move the answer.')

h2('Decision required')
tbl(['#', 'Decision', 'Who decides'],
    [['2.1', 'Whether this is a baseline for a later round, or an explanatory variable only',
      'Client'],
     ['2.2', 'WHO-5, or WHO-5 plus PHQ-2 and GAD-2', 'Client, on our recommendation'],
     ['2.3', 'Who secures the referral pathway with the County health department, and by when',
      'Client and County'],
     ['2.4', 'Whether the ethics amendment is submitted now or the measure is deferred',
      'Client — deferring is a legitimate choice if the timeline is tight']],
    widths=[1.2, 10.4, 5.0])

page_break()

# ================================================================ ITEM 3
h1('3.  Costing')

h2('What is missing')
body('The questionnaire tells us what parents want and what they are willing to pay. Nothing in '
     'the study tells us what any of the four options costs to run. Until that exists we can say '
     'which model traders prefer, but not which one the County can afford to keep running — and '
     '"the most sustainable model" is precisely the question the study is meant to answer.')
body('We have drafted a costing template as Section K of the questionnaire, marked in red. It is '
     'completed once per market and per provider, not administered to traders.')

h2('3.1  What it produces')
tbl(['Result', 'Why it matters'],
    [['Cost per child per day, for each model',
      'The number all four options can be compared on.'],
     ['Children needed to break even, at a price traders will pay',
      'If that number is higher than the children actually in the market, the model fails '
      'regardless of how much people like it.'],
     ['The shortfall the County must cover',
      'This is the budget line. The county interview asks whether a recurrent budget exists; '
      'this says how large it needs to be.'],
     ['The cost of making the space accessible, shown separately',
      'So the County can see what inclusion costs and decide who pays, instead of it '
      'disappearing into an average.']],
    widths=[6.0, 10.6])

h2('3.2  The mistake we need to avoid')
body('County-run will look cheapest, because the building is already owned and the ECDE staff '
     'are already on the payroll, so neither appears as a cost. If we let that stand, the '
     'comparison is not a comparison and the recommendation that comes out of it is wrong.')
rec('Enter the market rent for the space even where the County owns it, and the full salary cost '
    'including statutory contributions even where staff are seconded. The county interview '
    'already asks about secondment terms and salary scales, so the figures will be available.')

h2('3.3  What we cannot fill in yet')
body('About half the template can be completed from work already planned — the facility '
     'assessment gives us the space and its condition, and the county interview gives us '
     'standards, salary scales and budget lines. The other half cannot.')
flag('Running costs and fee collection rates can only come from someone already operating a '
     'daycare. There is no provider interview guide in the toolkit. Without one we can cost the '
     'county-run option from salary scales, but the private and partnership columns will be '
     'estimates we cannot defend.')
rec('Add a short provider interview guide and interview three to five operating daycares in or '
    'near these markets. It is a small piece of work and it is the difference between a costed '
    'comparison and an assumed one.')

h2('3.4  Testing whether the answer holds')
body('The recommendation should not rest on a single set of figures. We propose re-running the '
     'comparison while changing one assumption at a time: enrolment lower and higher, salaries '
     'higher, fees only partly collected, a better caregiver ratio, food included or not, rent '
     'charged or not, and the low season instead of a normal month.')
body('If the same model comes out best each time, the recommendation is solid. If the ranking '
     'changes, we tell the County which single figure they need to pin down before deciding — '
     'which is more useful to them than a confident number that turns out to be fragile.')

h2('Decision required')
tbl(['#', 'Decision', 'Who decides'],
    [['3.1', 'Section K is adopted as part of the toolkit', 'Client'],
     ['3.2', 'County-owned space and seconded staff will be costed at full value', 'Client'],
     ['3.3', 'Provider interviews are added, and who arranges access', 'Client and County'],
     ['3.4', 'Who in the County supplies salary scales, budget lines and construction rates',
      'County']],
    widths=[1.2, 10.4, 5.0])

page_break()

# ================================================================ CLOSING
h1('Consolidated actions')
h2('Before the meeting')
bullet('Confirm whether a follow-up survey round is planned — item 2.1 turns on it.', size=10.5)
bullet('Confirm the date of the county regulatory interview, since the choice experiment '
       'cannot be finalised before it.', size=10.5)
bullet('Ask the County who can provide ECDE salary scales and the market fee register.', size=10.5)

h2('Suggested order for the meeting')
tbl(['', 'Item', 'Time'],
    [['1', 'Choice experiment — attributes, levels, and the pilot sequence', '30 min'],
     ['2', 'Wellbeing measure — purpose, choice of measure, referral pathway', '20 min'],
     ['3', 'Costing — adopting Section K and adding provider interviews', '20 min'],
     ['4', 'Timeline and who does what', '10 min']],
    widths=[1.0, 12.6, 3.0])

h2('One housekeeping item')
body('Section B of the current questionnaire has four numbers used twice — B25, B26, B27 and '
     'B28 each appear both in the trading block and in the catchment block — and B27a still '
     'refers to B23. These will cause trouble at data entry. We will correct them when the '
     'instrument is signed off; no decision needed.')

add_footer()
doc.save(OUT)
print('saved', OUT)
