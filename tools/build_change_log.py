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
OUT = '/home/user/python/output/Questionnaire_Change_Log.docx'

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

p = doc.add_paragraph('CHANGE LOG', style='Title'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Every change made to the trader questionnaire, and why', size=12.5, bold=True,
     color=STEEL, after=2).alignment = WD_ALIGN_PARAGRAPH.CENTER
para('Gender-Responsive Childcare Services in Uasin Gishu County Markets  ·  '
     'From the reviewed draft through to the field-ready version',
     size=10, italic=True, color=GREY, after=14).alignment = WD_ALIGN_PARAGRAPH.CENTER

h2('Verdict on the current version')
callout('Ready for full collection:', 'Yes — the document is now sound. Every change below has '
        'been applied and checked. One thing is outside the document and must still be done: '
        'the four tablet settings in Section F0e have to be programmed into the Kobo form. The '
        'document instructs them; it cannot enforce them.', STEEL, '1F4D78')
action('Because the re-test has been dropped, a first-day check has been added at F0f. It uses '
       'the first 20 real interviews to confirm the tablet is shuffling the options. This is '
       'the only way left to catch a broken shuffle before it costs the whole survey, and it '
       'must be run before day two begins.')

h2('How the versions run')
tbl(['Version', 'What it was', 'Status'],
    [['Reviewed draft', 'Original questionnaire with reviewer comments in red and yellow',
      'Superseded'],
     ['v2', 'Reviewer recommendations resolved; sequential numbering', 'Superseded'],
     ['v3', 'Supplementary questions, wellbeing section, costing template, rebuilt choice cards',
      'Superseded'],
     ['v4', 'Pilot corrections to the choice experiment', 'Superseded'],
     ['v5 — FIELD READY', 'Numbering conflicts removed, timing restored, data-name annex added',
      'Use this one']],
    widths=[3.2, 9.4, 3.6])

page_break()
h1('Part 1 — Changes made before the pilot')
body('These came from reviewing the questionnaire against the study objectives. They were in '
     'place for the pilot.')

h2('1.1  Structure and numbering')
tbl(['Change', 'Why'],
    [['Every question numbered in sequence within its section',
      'The draft had gaps, repeats and items with no number at all. Skip instructions pointed '
      'at numbers that no longer existed.'],
     ['One coding convention throughout: 1 = Yes, 2 = No, 3 = Don\'t know, 4 = Refused',
      'The draft mixed 0/1 with 98/99 in different places, which produces two conventions in '
      'one dataset.'],
     ['All reviewer recommendations resolved into single questions',
      'The draft carried both the original and the proposed replacement for many items. A '
      'field instrument cannot ask both.'],
     ['Two overlapping child rosters merged into one',
      'A child qualifying on both criteria would have been entered twice.']],
    widths=[6.6, 9.6])

h2('1.2  Questions added to close gaps against the objectives')
tbl(['Added', 'What it covers', 'Why it was needed'],
    [['B31–B34', 'Where the trader lives, how they travel, journey time, whether a child '
      'travels with them',
      'The study asked how far a centre could be from the stall but never where the trader '
      'starts from.'],
     ['C14, C15', 'Whether they have ever paid for childcare; hours of care needed per week',
      'Past payment is the strongest anchor for what someone will pay. Hours convert a '
      'building\'s capacity into actual places.'],
     ['E6', 'Seven statements on norms and attitudes',
      'The methodology promised to examine norms around childcare and women working. Only the '
      'focus groups touched it.'],
     ['G8–G12', 'Expected change in trading, preferred payment method, and a market-levy option',
      'The study measured what childcare costs but never what it returns, and tested only one '
      'way of paying for it.'],
     ['H15–H18', 'Whether inclusion should be mandatory, who pays for accessibility, NCPWD '
      'registration, drop-off support',
      'The objective asks how models should be structured for inclusion. Officials were asked; '
      'traders were not.'],
     ['Section J', 'WHO-5 wellbeing, five items',
      'The only benefit measured was trading days recovered. Wellbeing is part of the return.'],
     ['Section L', 'Costing template',
      'Nothing in the study collected what any of the four models costs to run.']],
    widths=[2.4, 6.4, 7.4])

h2('1.3  The choice cards were rebuilt')
tbl(['Old', 'New', 'Why'],
    [['12 cards, 2 blocks', '18 cards, 3 blocks, still 6 per trader',
      'The software rejects a design with fewer cards than parameters. Respondent burden is '
      'unchanged.'],
     ['6 of 12 cards differed on all 7 features', 'All 18 differ on all 7',
      'One old card differed on only four features; another had the same price on both sides.'],
     ['Trader-committee option on 2 of 12 cards', '3 times in every block',
      'Two appearances cannot support an estimate, and comparing the four models is a main '
      'purpose of the study.'],
     ['No check on one-sided cards', 'No card offers an option better in every way',
      'A card with no trade-off tells you nothing.']],
    widths=[4.6, 5.4, 6.2])

page_break()
h1('Part 2 — Changes made after the pilot')
body('These come from re-analysing the 23 pilot interviews. Each one is tied to a specific '
     'result, not to preference.')

h2('2.1  The choice experiment — four changes (Section F0e)')
tbl(['#', 'Change', 'What the pilot showed', 'What it prevents'],
    [['1', 'The tablet shuffles which option appears first, on every card',
      'On 9 of the 12 cards used, the cheaper option was on the left. Traders chose the left '
      'option 59% of the time.',
      'Price and position being the same thing, which is why no price finding can be reported '
      'from the pilot'],
     ['2', 'The form records which way round it showed them',
      'Nothing recorded the order, so the effect could be seen but not corrected',
      'Being stuck again. Even if something else goes wrong, it can now be measured and '
      'adjusted for'],
     ['3', 'Block stored as 1, 2 or 3 rather than as text',
      'The pilot stored "Block 1 (Odd-numbered IDs)"',
      'An analysis that cannot tell which cards a trader saw'],
     ['4', 'Straight-lining flagged while the enumerator is still present, recorded at F11',
      '4 of 23 traders chose the same side on all six cards. Removing those four made the '
      'position effect disappear.',
      'Finding out months later, when nothing can be done']],
    widths=[0.8, 4.2, 5.6, 5.6])

h2('2.2  Scales that turned out not to be scales')
tbl(['Item', 'What the pilot showed', 'What changed'],
    [['E1h — locked and secure entry', 'Every single trader gave the same answer',
      'Kept as a standalone question, excluded from any combined score. A question everyone '
      'answers identically cannot distinguish between people.'],
     ['E1a–E1l as a set', 'Reliability 0.48; three quarters of answers sat at the top of the scale',
      'Reported item by item, not summed. Traders say everything is important, so the choice '
      'cards do this job better.'],
     ['E6a–E6g as a set', 'Reliability looks acceptable at 0.60 but collapses to 0.05 once the '
      'two reverse-worded items are corrected',
      'Reported item by item. E6c and E6f behaved well and are kept as individual indicators.']],
    widths=[3.6, 5.8, 6.8])

h2('2.3  Fixes applied in this final version')
tbl(['Fix', 'The problem', 'What was done'],
    [['Duplicate question numbers',
      'B25, B26, B27 and B28 each appeared twice — once in the trading block and again in the '
      'catchment block',
      'The catchment block is now B31–B34, which also matches the tablet form'],
     ['Wrong cross-reference', 'B27a told the enumerator to enter a code from B23',
      'Corrected to B27'],
     ['No interview timing', 'Length was taken from when the form was opened and closed. Three '
      'interviews showed as over three hours, one as eighteen.',
      'K6 and K7 added to record start and end directly'],
     ['Re-test declined', 'The shuffle cannot be verified from existing data',
      'F0f added: a check on the first 20 interviews that does the same job'],
     ['Document and tablet number questions differently',
      'What this document calls B25, the data calls B27. Anyone using the document as a '
      'codebook would mis-map the data.',
      'Annex M lists the tablet field names. The tablet was left alone because it has already '
      'collected data under those names.']],
    widths=[3.4, 6.4, 6.4])

page_break()
h1('Part 3 — What still sits outside this document')
body('These are not questionnaire problems and cannot be fixed by editing it.')
tbl(['Item', 'Status', 'Consequence if not done'],
    [['Programme the four tablet settings (F0e)', 'NOT DONE — required before the next interview',
      'The full survey repeats the pilot\'s central fault and the price finding is lost again'],
     ['Run the first-day check (F0f)', 'Required before day two',
      'A broken shuffle would not be caught until analysis'],
     ['Confirm with the County whether the two lowest service levels are lawful',
      'Outstanding',
      'We may be asking traders to price a service that could not legally be offered'],
     ['Write the provider interview guide', 'Does not exist',
      'The costing template cannot be filled for private and partnership models'],
     ['Fill the costing template with real figures', 'Empty',
      'Objective iv — which model is most sustainable — cannot be answered at all'],
     ['Decide the subgroup question', 'Outstanding',
      'At 300 interviews, women can be analysed separately but men cannot. A proper comparison '
      'needs about 400 with a quota.']],
    widths=[4.6, 4.0, 7.6])
finding('The first two rows are the ones that decide whether the full survey succeeds. The last '
        'three decide whether the study can answer all four of its objectives or only three.')

h2('One honest note on dropping the re-test')
body('The re-test was the safest way to confirm the shuffle works, and it has been dropped. The '
     'first-day check at F0f is a reasonable substitute and costs nothing extra, but it differs '
     'in one way worth stating plainly: it catches the problem after 20 real interviews rather '
     'than before any. If the shuffle is broken, those 20 interviews are compromised and would '
     'need to be set aside or re-done. That is the risk being accepted, and it is a small one '
     'against a full survey of 300.')

add_footer(); doc.save(OUT); print('saved', OUT)
