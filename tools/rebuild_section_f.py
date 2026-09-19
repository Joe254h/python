# -*- coding: utf-8 -*-
"""Replace Section F with a regenerated, field-ready choice-card set."""
import json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

SRC = ('/root/.claude/uploads/920ad5d8-6e07-5909-9e17-40c3ac0fe128/'
       '34267fa2-Trader_Questionnaire_FULL.docx')
OUT = '/home/user/python/output/Trader_Questionnaire_FULL_v2.docx'
CARDS = json.load(open('/home/user/python/output/r/dce_design_cards.json'))

F = 'Calibri'
NAVY  = RGBColor(0x1F, 0x38, 0x64)
STEEL = RGBColor(0x1F, 0x4D, 0x78)
GREY  = RGBColor(0x59, 0x59, 0x59)
RED   = RGBColor(0xC0, 0x00, 0x00)
BLACK = RGBColor(0x00, 0x00, 0x00)

doc = Document(SRC)
body = doc.element.body

def content(b):
    return [el for el in b if el.tag != qn('w:sectPr')]

# ---------- locate Section F and Section G -----------------------------------
kids = content(body)
fi = gi = None
for i, el in enumerate(kids):
    if el.tag == qn('w:p'):
        t = Paragraph(el, doc).text.strip()
        if t == 'Section F — Discrete choice experiment':
            fi = i
        elif t == 'Section G — Willingness to pay':
            gi = i; break
assert fi is not None and gi is not None, (fi, gi)
old = kids[fi:gi]
g_el = kids[gi]
print(f'removing {len(old)} elements of the old Section F')
for el in old:
    body.remove(el)

# ---------- builders ----------------------------------------------------------
n_before = len(content(body))

def run(p, text, size=11, bold=False, italic=False, color=BLACK):
    r = p.add_run(text)
    r.font.name = F; r.font.size = Pt(size)
    r.font.bold = bold; r.font.italic = italic; r.font.color.rgb = color
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rf.set(qn(a), F)
    return r

def para(text='', size=11, bold=False, italic=False, color=BLACK,
         before=0, after=4, indent=0, align=None, keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.keep_with_next = keep
    if indent: p.paragraph_format.left_indent = Cm(indent)
    if align is not None: p.alignment = align
    if text: run(p, text, size, bold, italic, color)
    return p

def h1(text):
    p = para(text, size=15, bold=True, color=NAVY, before=16, after=8, keep=True)
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement('w:pBdr'); bo = OxmlElement('w:bottom')
    bo.set(qn('w:val'), 'single'); bo.set(qn('w:sz'), '6')
    bo.set(qn('w:space'), '4'); bo.set(qn('w:color'), '1F3864')
    b.append(bo); pPr.append(b)
    return p

def h2(text, color=STEEL):
    return para(text, size=12.5, bold=True, color=color, before=12, after=5, keep=True)

def instr(text, color=GREY):
    return para(text, size=10, italic=True, color=color, before=2, after=5, indent=0.5)

def bullet(text, size=10.5):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(1.0)
    run(p, text, size)
    return p

def shade(cell, hexval):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexval)
    tcPr.append(sh)

def nosplit(t):
    for r in t.rows:
        trPr = r._tr.get_or_add_trPr()
        e = OxmlElement('w:cantSplit'); trPr.append(e)

def cell(c, text, bold=False, size=10, color=BLACK, align=None, valign=True):
    c.text = ''
    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(3)
    if align is not None: p.alignment = align
    if text: run(p, text, size, bold, color=color)
    if valign:
        tcPr = c._tc.get_or_add_tcPr()
        va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); tcPr.append(va)
    return p

def page_break():
    p = doc.add_paragraph()
    r = p.add_run(); r._element.append(OxmlElement('w:br'))
    r._element[-1].set(qn('w:type'), 'page')

ATTR_ROWS = [
    ('cost',      'Cost'),
    ('location',  'Location'),
    ('hours',     'Opening hours'),
    ('care',      'Caregiver ratio & training'),
    ('food',      'Food'),
    ('operator',  'Who runs it'),
    ('inclusion', 'Inclusiveness of facilities'),
]
SHORT = {
 'cost': lambda v: v.replace('KES ', '').replace('/day', ' shillings'),
 'location': lambda v: {'Inside the market, next to the stalls': 'inside the market',
                        '5-minute walk': '5-minute walk',
                        '15-minute walk': '15-minute walk'}[v],
 'hours': lambda v: v.replace('–', ' to ').replace(':00', ''),
 'care': lambda v: {'1 trained caregiver per 5 children': 'one trained per five',
                    '1 trained caregiver per 10 children': 'one trained per ten',
                    '1 untrained helper per 10 children': 'one untrained per ten'}[v],
 'food': lambda v: 'food provided' if v.startswith('Porridge') else 'bring own food',
 'operator': lambda v: {'County staff; complaints go to the county office': 'county-run',
   'Private operator paying rent; operator sets fees; complaints go to the operator':
       'private operator',
   'County and private operator jointly agree fees; complaints go to a joint office':
       'county and operator together',
   'Committee of market traders; complaints go to the committee': 'traders’ committee'}[v],
 'inclusion': lambda v: {
   'Physically accessible with staff trained to support children with disabilities':
       'accessible, trained staff',
   'Physically accessible (ramp, adapted toilet), staff not disability-trained':
       'accessible, staff not trained',
   'No special accommodation for children with disabilities': 'no accommodation'}[v],
}
# match the questionnaire's existing wording for the PPP level
FIXWORD = {'County and private operator jointly agree fees; complaints go to a joint office':
           'County and private operator jointly agree on fees; complaints go to a joint office'}
def wording(v):
    return FIXWORD.get(v, v)

# ================================================================= SECTION F
h1('Section F — Discrete choice experiment')
para('Field instrument — pilot version (n = 30).  Uasin Gishu market childcare study.',
     size=10, italic=True, color=GREY, after=8)

# --- first-person note on what changed -------------------------------------
p = para('', before=4, after=10)
p.paragraph_format.left_indent = Cm(0.5)
pPr = p._p.get_or_add_pPr()
b = OxmlElement('w:pBdr'); e = OxmlElement('w:left')
e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '18')
e.set(qn('w:space'), '8'); e.set(qn('w:color'), 'C00000')
b.append(e); pPr.append(e) if False else pPr.append(b)
run(p, 'Note on this version:  ', size=10.5, bold=True, color=RED)
run(p, 'I have replaced the choice cards. The previous set had twelve cards in two '
       'blocks, and several of them asked the respondent to compare two options that '
       'were nearly the same — one card differed on only four of the seven features, '
       'another had the same price on both sides. The trader-committee option appeared '
       'on just two of the twelve cards, which is too few to estimate how traders feel '
       'about it. The design software also rejected twelve cards outright: it needs at '
       'least as many cards as there are things being estimated, which is fifteen here.',
    size=10.5, color=RED)
p2 = para('', before=0, after=10)
p2.paragraph_format.left_indent = Cm(0.5)
pPr2 = p2._p.get_or_add_pPr()
b2 = OxmlElement('w:pBdr'); e2 = OxmlElement('w:left')
e2.set(qn('w:val'), 'single'); e2.set(qn('w:sz'), '18')
e2.set(qn('w:space'), '8'); e2.set(qn('w:color'), 'C00000')
b2.append(e2); pPr2.append(b2)
run(p2, 'This set has eighteen cards in three blocks. Each trader still answers only '
        'six, so the interview is no longer than before. Every card now differs on all '
        'seven features, no card offers one option that is simply better than the other '
        'in every way, and each block carries all four management models three times. '
        'I have also printed the short reading version under each card so nobody has to '
        'improvise it.', size=10.5, color=RED)

# --- F0 model show-card ------------------------------------------------------
h2('F0.  Model description show-card — read once, before Set 1')
instr('Read all four descriptions aloud, in the same order and the same tone, before '
      'the first choice set. Every respondent must hear the same description. Do not '
      'add examples of your own and do not indicate which model the County favours.')
mrows = [
 ('County-run', 'The County owns and runs the space.', 'County staff, employed by the County',
  'The County sets the fee', 'The county office', 'The County pays', 'The County'),
 ('Private operator', 'A private business rents the space from the County and runs it.',
  'Employed by the operator', 'The operator sets the fee', 'The operator',
  'The operator pays, under the rental agreement', 'The operator'),
 ('Public–private partnership', 'The County and a private operator run it jointly under an agreement.',
  'Employed by the operator, to County standards', 'The County and operator agree the fee jointly',
  'A joint office', 'Shared, as set out in the agreement', 'The County and operator jointly'),
 ('Market-trader committee', 'The traders’ own committee runs the space.', 'Hired by the committee',
  'The committee sets the fee', 'The committee', 'The committee raises the money', 'The committee'),
]
t = doc.add_table(rows=5, cols=7); t.style = 'Table Grid'
t.alignment = WD_TABLE_ALIGNMENT.LEFT; t.autofit = False
widths = [2.5, 3.3, 2.5, 2.4, 1.9, 2.4, 1.9]
for r in t.rows:
    for i, w in enumerate(widths): r.cells[i].width = Cm(w)
for i, lab in enumerate(['Model', 'How it works', 'Caregivers', 'Who sets the fee',
                         'Complaints go to', 'Major repairs', 'Accessibility duty']):
    cell(t.rows[0].cells[i], lab, bold=True, size=8.5, color=RGBColor(0xFF,0xFF,0xFF),
         align=WD_ALIGN_PARAGRAPH.CENTER)
    shade(t.rows[0].cells[i], '1F4D78')
for i, r in enumerate(mrows, start=1):
    cell(t.rows[i].cells[0], r[0], bold=True, size=9)
    for j in range(1, 7): cell(t.rows[i].cells[j], r[j], size=8.5)
    if i % 2 == 0:
        for j in range(7): shade(t.rows[i].cells[j], 'F2F6FA')
nosplit(t)
instr('These columns deliberately mirror the “Who runs it” levels on the cards and the '
      'functions listed in E4, so the three can be read together.')

# --- F0a design spec ---------------------------------------------------------
h2('F0a.  Design specification')
spec = [('Attributes', 'Seven: cost, location, opening hours, caregiver ratio and '
                       'training, food, who runs it, inclusion'),
        ('Alternatives', 'Two unlabelled options plus an opt-out ("I would use neither; '
                         'I’d keep my current arrangement")'),
        ('Choice sets', '18, blocked into 3 blocks of 6'),
        ('Seen per respondent', '6 cards'),
        ('Criterion', 'D-efficient, generated by coordinate exchange with zero priors'),
        ('Constraints applied', 'No two options on a card identical; no option better '
                                'than the other on every feature; all four management '
                                'models equally represented in every block')]
t = doc.add_table(rows=len(spec), cols=2); t.style = 'Table Grid'
t.alignment = WD_TABLE_ALIGNMENT.LEFT; t.autofit = False
for r in t.rows:
    r.cells[0].width = Cm(4.2); r.cells[1].width = Cm(12.4)
for i, (k, v) in enumerate(spec):
    cell(t.rows[i].cells[0], k, bold=True, size=9.5)
    cell(t.rows[i].cells[1], v, size=9.5)
nosplit(t)
instr('This pilot design uses assumed priors, not priors estimated from data. Pilot the '
      'cards with 30 respondents, check the enumerator flags at F7–F9, estimate '
      'preliminary preferences, and regenerate before printing the main-survey version.')
para('The cards still contain "1 untrained helper per 10 children" and "no special '
     'accommodation for children with disabilities". They are kept so the pilot runs on '
     'the design as drafted. If the County confirms these fall below the enforced '
     'minimum standard (KII section 1), drop them when the design is regenerated.',
     size=10, italic=True, color=RED, indent=0.5, after=6)

# --- F0b cheap talk ----------------------------------------------------------
h2('F0b.  Cheap-talk script — read once, before Set 1 only')
p = para('', before=2, after=6, indent=0.5)
run(p, '“People often say they would pay more for something than they actually do when '
       'the time comes. Please answer as if this money were really coming out of '
       'today’s sales.”', size=11.5, italic=True)
instr('Read this once, immediately before the first card — not before every set. '
      'Without it a trader may agree to a price because no money is actually leaving '
      'her pocket; with it she weighs the amount against today’s takings.')

# --- F0c reading instructions -------------------------------------------------
h2('F0c.  How to read a card')
bullet('Sets 1 and 2: read every row aloud in full for both options, pointing at each '
       'icon as you name it.')
bullet('Sets 3 to 6: read the short version printed under the card. The respondent has '
       'seen the format twice by then and the card carries the detail.')
bullet('Read the third option — “I would use neither; I’d keep my current arrangement” — '
       'every single time, in the same place and the same tone as the other two. If you '
       'read A and B carefully but rush “or neither”, respondents learn it is not a real '
       'option and you get fewer honest opt-outs than you should.')
bullet('Never say which option you would pick, and never explain a feature beyond the '
       'words on the card.')

# --- F0d block assignment -----------------------------------------------------
h2('F0d.  Assigning a respondent to a block')
para('Each respondent answers ONE block of six cards. Assign by respondent ID:',
     size=11, after=4)
t = doc.add_table(rows=2, cols=4); t.style = 'Table Grid'
t.alignment = WD_TABLE_ALIGNMENT.LEFT; t.autofit = False
for r in t.rows:
    for i, w in enumerate([5.6, 3.6, 3.6, 3.6]): r.cells[i].width = Cm(w)
cell(t.rows[0].cells[0], 'Respondent ID ends in', bold=True, size=9.5,
     color=RGBColor(0xFF,0xFF,0xFF)); shade(t.rows[0].cells[0], '1F4D78')
for i, lab in enumerate(['1, 4, 7 …', '2, 5, 8 …', '3, 6, 9 …'], start=1):
    cell(t.rows[0].cells[i], lab, bold=True, size=9.5, color=RGBColor(0xFF,0xFF,0xFF),
         align=WD_ALIGN_PARAGRAPH.CENTER)
    shade(t.rows[0].cells[i], '1F4D78')
cell(t.rows[1].cells[0], 'Show', bold=True, size=9.5)
for i, lab in enumerate(['Block 1', 'Block 2', 'Block 3'], start=1):
    cell(t.rows[1].cells[i], lab, bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
nosplit(t)
instr('In other words, block = the remainder when you divide the respondent ID by 3 '
      '(with 0 meaning Block 3). Record the block number on the cover sheet — the '
      'analysis needs to know which cards the respondent saw.')

# --- the cards ----------------------------------------------------------------
BLOCK_SHADE = {1: 'EEF3F9', 2: 'F1F7F1', 3: 'FBF3EC'}
by_block = {}
for r in CARDS['sets']:
    by_block.setdefault(r['block'], []).append(r)

for blk in sorted(by_block):
    page_break()
    p = para('', before=0, after=8)
    run(p, f'Block {blk}', size=16, bold=True, color=NAVY)
    run(p, f'   —   show to respondents whose ID divided by 3 leaves '
           f'{blk if blk < 3 else 0}', size=11, italic=True, color=GREY)

    for n, rec in enumerate(by_block[blk], start=1):
        # card header
        hp = para('', before=10, after=0, keep=True)
        run(hp, f'F{n}.', size=12.5, bold=True, color=NAVY)
        run(hp, f'   Set {n} of 6', size=12.5, bold=True)
        run(hp, f'      (design set {rec["set"]})', size=9, italic=True, color=GREY)

        t = doc.add_table(rows=8, cols=3); t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.LEFT; t.autofit = False
        for r in t.rows:
            for i, w in enumerate([4.4, 6.1, 6.1]): r.cells[i].width = Cm(w)
        for i, lab in enumerate(['Attribute', 'Alternative A', 'Alternative B']):
            cell(t.rows[0].cells[i], lab, bold=True, size=10,
                 color=RGBColor(0xFF,0xFF,0xFF), align=WD_ALIGN_PARAGRAPH.CENTER)
            shade(t.rows[0].cells[i], '1F4D78')
        for i, (key, lab) in enumerate(ATTR_ROWS, start=1):
            cell(t.rows[i].cells[0], lab, bold=True, size=10)
            cell(t.rows[i].cells[1], wording(rec['A'][key]), size=10)
            cell(t.rows[i].cells[2], wording(rec['B'][key]), size=10)
            if i % 2 == 1:
                for j in range(3): shade(t.rows[i].cells[j], BLOCK_SHADE[blk])
        nosplit(t)

        cp = para('', before=4, after=2)
        run(cp, 'Which would you choose?      ', size=11, bold=True)
        run(cp, '☐ 1 = Alternative A       ☐ 2 = Alternative B       '
                '☐ 3 = Neither — I’d keep my current arrangement', size=11)

        sa = ', '.join(SHORT[k](rec['A'][k]) for k, _ in ATTR_ROWS)
        sb = ', '.join(SHORT[k](rec['B'][k]) for k, _ in ATTR_ROWS)
        sp = para('', before=2, after=8, indent=0.3)
        run(sp, 'Short version — ', size=9, bold=True, color=GREY)
        run(sp, f'A: {sa}.   B: {sb}.', size=9, italic=True, color=GREY)

# --- enumerator checks ---------------------------------------------------------
page_break()
h2('Enumerator checks — ask after the last card', color=NAVY)
def q(num, text, codes=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(1.05)
    p.paragraph_format.first_line_indent = Cm(-1.05)
    p.paragraph_format.keep_with_next = True
    run(p, num + '  ', bold=True); run(p, text)
    if codes:
        c = doc.add_paragraph()
        c.paragraph_format.space_before = Pt(0); c.paragraph_format.space_after = Pt(3)
        c.paragraph_format.left_indent = Cm(1.05)
        run(c, codes, size=10.5)

q('F7.', 'Non-trading check: did the respondent pick the cheapest alternative in every '
         'single card of their block, even where the quality gap looked large?',
  '1 = Yes    2 = No')
instr('Not necessarily an error, but flag it on the cover sheet for review.')
q('F8.', 'Opt-out check: did the respondent pick “Neither” on every card?',
  '1 = Yes    2 = No')
q('F8a.', 'If F8 = 1, ask: “Can you tell me why you would keep your current arrangement '
          'rather than any of these?”  Record verbatim.')
for _ in range(2):
    para('_' * 92, size=10, indent=1.05, after=2)
q('F9.', 'Attribute non-attendance: “Was there any part of these cards — the cost, the '
         'distance, the hours, the caregivers, the food, who runs it, or the '
         'accessibility — that you ignored when choosing?”  (tick all that were ignored)',
  '1 = Cost   2 = Location   3 = Opening hours   4 = Caregiver ratio / training   '
  '5 = Food   6 = Who runs it   7 = Inclusiveness   8 = None ignored')
q('F10.', 'Which block did this respondent answer?', '1 = Block 1   2 = Block 2   3 = Block 3')
instr('Added: with three blocks this must be recorded, or the analysis cannot tell which '
      'cards the respondent saw.')
page_break()

# ---------- move the new content into place ----------------------------------
new = content(body)[n_before:]
for el in new:
    body.remove(el); g_el.addprevious(el)

doc.save(OUT)
print('saved', OUT)
