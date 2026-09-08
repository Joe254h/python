# -*- coding: utf-8 -*-
"""Append the costing template to the client's final questionnaire, all in red.
Existing content is untouched — the file is opened and added to, not rebuilt."""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = ('/root/.claude/uploads/920ad5d8-6e07-5909-9e17-40c3ac0fe128/'
       '5fa866ff-Trader_Questionnaire_Integrated_edited_final_final.docx')
OUT = '/home/user/python/output/Trader_Questionnaire_with_Costing_Template.docx'

F = 'Calibri'
RED = RGBColor(0xC0, 0x00, 0x00)
doc = Document(SRC)

def run(p, text, size=11, bold=False, italic=False):
    r = p.add_run(text)
    r.font.name = F; r.font.size = Pt(size)
    r.font.bold = bold; r.font.italic = italic; r.font.color.rgb = RED
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rf.set(qn(a), F)
    return r

def para(text='', size=11, bold=False, italic=False, before=0, after=4, indent=0,
         align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        run(p, text, size, bold, italic)
    return p

def h1(text):
    p = para(text, size=15, bold=True, before=16, after=8)
    p.paragraph_format.keep_with_next = True
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement('w:pBdr'); bo = OxmlElement('w:bottom')
    bo.set(qn('w:val'), 'single'); bo.set(qn('w:sz'), '6')
    bo.set(qn('w:space'), '4'); bo.set(qn('w:color'), 'C00000')
    b.append(bo); pPr.append(b)
    return p

def h2(text):
    p = para(text, size=12.5, bold=True, before=12, after=5)
    p.paragraph_format.keep_with_next = True
    return p

def q(num, text, codes=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(1.05)
    p.paragraph_format.first_line_indent = Cm(-1.05)
    p.paragraph_format.keep_with_next = True
    run(p, num + '  ', bold=True)
    run(p, text)
    if codes:
        c = doc.add_paragraph()
        c.paragraph_format.space_before = Pt(0); c.paragraph_format.space_after = Pt(3)
        c.paragraph_format.left_indent = Cm(1.05)
        run(c, codes, size=10.5)
    return p

def instr(text):
    return para(text, size=10, italic=True, before=2, after=4, indent=1.05)

def shade(cell, hexval):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexval)
    tcPr.append(sh)

def cell(c, text, bold=False, size=9.5, align=None):
    c.text = ''
    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
    if align is not None:
        p.alignment = align
    if text:
        run(p, text, size=size, bold=bold)
    return p

def grid(header, rows, widths, blank_rows=0, size=9.5):
    t = doc.add_table(rows=len(rows) + blank_rows + 1, cols=len(header))
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.LEFT; t.autofit = False
    for r in t.rows:
        for i, w in enumerate(widths):
            r.cells[i].width = Cm(w)
    for i, lab in enumerate(header):
        cell(t.rows[0].cells[i], lab, bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER)
        shade(t.rows[0].cells[i], 'FBE4E4')
    trPr = t.rows[0]._tr.get_or_add_trPr()
    el = OxmlElement('w:tblHeader'); el.set(qn('w:val'), 'true'); trPr.append(el)
    for ri, row in enumerate(rows, start=1):
        for ci, val in enumerate(row):
            cell(t.rows[ri].cells[ci], val, bold=(ci == 0 and val != ''), size=size)
    for ri in range(len(rows) + 1, len(rows) + 1 + blank_rows):
        for ci in range(len(header)):
            cell(t.rows[ri].cells[ci], '', size=size)
            t.rows[ri].cells[ci].paragraphs[0].paragraph_format.space_after = Pt(5)
    return t

KES = 'Amount (KES)'
NOTE = 'Source / note'

doc.add_page_break()

h1('Section K — Childcare Costing Template')
para('Everything in this section is new. It is printed in red so it can be told apart from the '
     'questionnaire above.', size=10, italic=True, after=8)

h2('Why this section exists')
para('The questionnaire tells us what parents want and what they are willing to pay. It does not '
     'tell us what any of the four options costs to run. Without that, we can say which model '
     'traders prefer, but not which one the County can afford to keep running. This section '
     'collects the missing half.', after=6)
para('It is not administered to traders. It is completed once per market and per provider, using '
     'figures from existing childcare providers, County departments, and supplier quotations.',
     after=6)

h2('Who provides each figure')
grid(['Information needed', 'Who to get it from'],
     [['Space, condition, water, sanitation, power, safety',
       'Facility assessment tool, sections 2–9'],
      ['Space standard per child, staff ratios, caregiver qualifications, licence fees',
       'County KII, section 1'],
      ['ECDE staff salary scale, secondment terms, budget line',
       'County KII, section 3'],
      ['Accessibility works needed, and whether already budgeted',
       'Facility assessment section 8; County KII section 7'],
      ['Actual salaries, food, utilities, enrolment and fee collection',
       'Existing childcare providers (KII)'],
      ['Construction and retrofit unit rates',
       'County public works; supplier quotations'],
      ['What parents will pay, and how', 'Questionnaire sections F and G']],
     widths=[8.4, 7.8])

h2('K1.  Identification')
grid(['Item', 'Record here'],
     [['K1a.  Market', ''], ['K1b.  Model being costed', 'County / Private / PPP / Committee'],
      ['K1c.  Source of these figures', ''], ['K1d.  Date and person completing', '']],
     widths=[6.4, 9.8])

h2('K2.  One-off (capital) costs')
instr('Record what it would cost to bring this specific space into use. Use measured figures '
      'from the facility assessment, not estimates.')
grid(['Item', KES, 'Expected life (years)', NOTE],
     [['K2a.  Building repair or conversion', '', '', ''],
      ['K2b.  Water connection or tank', '', '', ''],
      ['K2c.  Toilets and handwashing', '', '', ''],
      ['K2d.  Kitchen / food preparation', '', '', ''],
      ['K2e.  Safety works (lockable door, controlled entry, fencing)', '', '', ''],
      ['K2f.  Electrical works and lighting', '', '', ''],
      ['K2g.  Furniture, mats, cots, play materials', '', '', ''],
      ['K2h.  Initial caregiver training and certification', '', '', ''],
      ['K2i.  Registration and licensing fees', '', '', ''],
      ['K2j.  Other (specify)', '', '', ''],
      ['K2k.  TOTAL one-off cost', '', '', '']],
     widths=[7.0, 2.9, 2.9, 3.4])

h2('K3.  Cost of making the space accessible to all children')
instr('Keep this separate from K2. The County needs to see what inclusion costs on its own, so '
      'it can decide who pays for it rather than losing it inside an average.')
grid(['Item', KES, NOTE],
     [['K3a.  Ramp', '', ''],
      ['K3b.  Widening doors to 800mm or more', '', ''],
      ['K3c.  Accessible toilet', '', ''],
      ['K3d.  Levelling the route from the stalls', '', ''],
      ['K3e.  Disability-inclusion training for caregivers', '', ''],
      ['K3f.  Additional caregiver time (lower ratio)', '', ''],
      ['K3g.  Other (specify)', '', ''],
      ['K3h.  TOTAL inclusion cost — one-off', '', ''],
      ['K3i.  TOTAL inclusion cost — per year', '', '']],
     widths=[7.6, 3.6, 5.0])

h2('K4.  Staff costs, per month')
instr('Number of staff follows from the caregiver-to-child ratio the County enforces and the '
      'ratio tested on the choice cards. Include statutory contributions — they are a real cost.')
grid(['Role', 'Number', 'Pay each, per month', 'Statutory add-ons (NSSF, SHA, leave)',
      'Monthly total'],
     [['K4a.  Trained caregivers', '', '', '', ''],
      ['K4b.  Assistants / untrained helpers', '', '', '', ''],
      ['K4c.  Supervisor or manager', '', '', '', ''],
      ['K4d.  Cook', '', '', '', ''],
      ['K4e.  Cleaner', '', '', '', ''],
      ['K4f.  Security', '', '', '', ''],
      ['K4g.  TOTAL staff cost per month', '', '', '', '']],
     widths=[4.8, 1.9, 3.2, 3.7, 2.6])

h2('K5.  Running costs, per month')
grid(['Item', KES, NOTE],
     [['K5a.  Food (porridge and lunch)', '', 'Per child per day × children × days'],
      ['K5b.  Water', '', ''],
      ['K5c.  Electricity', '', ''],
      ['K5d.  Cleaning and consumables', '', ''],
      ['K5e.  First aid and medical supplies', '', ''],
      ['K5f.  Rent or space charge', '', 'Enter market rent even where the County owns the space'],
      ['K5g.  Repairs and maintenance', '', 'See E4 — who carries this under each model'],
      ['K5h.  Insurance (public liability)', '', 'Usually required for licensing'],
      ['K5i.  Licence renewal', '', ''],
      ['K5j.  Administration and management', '', ''],
      ['K5k.  Cost of collecting fees', '', 'Matters most under the committee model'],
      ['K5l.  Other (specify)', '', ''],
      ['K5m.  TOTAL running cost per month', '', '']],
     widths=[6.2, 3.2, 6.8])

h2('K6.  How many children, and for how long')
grid(['Item', 'Record here'],
     [['K6a.  Places available (floor area ÷ County space standard)', ''],
      ['K6b.  Children expected per day', ''],
      ['K6c.  Average attendance rate (%)', ''],
      ['K6d.  Hours open per day', ''],
      ['K6e.  Days open per year', ''],
      ['K6f.  Average hours each child needs per week', 'From questionnaire C15'],
      ['K6g.  Expected enrolment in the low season', 'Traders trade fewer days in some months']],
     widths=[9.0, 7.2])

h2('K7.  Money coming in, per month')
grid(['Source', KES, NOTE],
     [['K7a.  Fees from parents', '', 'Price × children × days × collection rate'],
      ['K7b.  Expected collection rate (%)', '', 'From questionnaire G10 and G11'],
      ['K7c.  Market levy, if used', '', 'From G12a × number of traders in the market'],
      ['K7d.  County subsidy', '', ''],
      ['K7e.  Donor or NGO support', '', ''],
      ['K7f.  TOTAL income per month', '', '']],
     widths=[6.2, 3.2, 6.8])

h2('K8.  What differs between the four models')
instr('Fill one column per model. County-run will look cheapest unless the building and the '
      'seconded staff are entered at what they actually cost — enter them, or the comparison '
      'is not a fair one.')
grid(['', 'County-run', 'Private operator', 'Partnership', 'Trader committee'],
     [['K8a.  Rent charged', '', '', '', ''],
      ['K8b.  Who employs and pays the caregivers', '', '', '', ''],
      ['K8c.  Overheads carried elsewhere', '', '', '', ''],
      ['K8d.  Operator margin required', '', '', '', ''],
      ['K8e.  Who funds the one-off costs', '', '', '', ''],
      ['K8f.  Who pays major repairs', '', '', '', ''],
      ['K8g.  Who carries unpaid fees', '', '', '', '']],
     widths=[4.6, 2.9, 2.9, 2.9, 2.9])

h2('K9.  The four numbers this produces')
instr('Calculate these for each model. They are what the comparison of the four options rests on.')
grid(['Result', 'How it is worked out', 'County', 'Private', 'Partnership', 'Committee'],
     [['K9a.  Cost per child per day',
       '(One-off ÷ life ÷ days) + (monthly running ÷ children ÷ days)', '', '', '', ''],
      ['K9b.  Children needed to break even',
       'Monthly costs ÷ (fee × days × collection rate)', '', '', '', ''],
      ['K9c.  Shortfall the County must cover',
       'Total cost − total income, per month and per year', '', '', '', ''],
      ['K9d.  Cost of inclusion',
       'K3h and K3i, shown separately', '', '', '', '']],
     widths=[3.4, 4.6, 2.05, 2.05, 2.05, 2.05])

h2('K10.  Testing how solid the answer is')
instr('Re-run K9 changing one thing at a time. If the same model comes out best every time, the '
      'recommendation is safe. If the ranking changes, we tell the County which single figure '
      'they need to pin down before deciding.')
grid(['Change', 'Does the best model change?'],
     [['K10a.  Enrolment 30% lower, and 30% higher', ''],
      ['K10b.  Salaries 20% higher', ''],
      ['K10c.  Only 80%, then 60%, of fees actually collected', ''],
      ['K10d.  One caregiver to 5 children instead of 1 to 10', ''],
      ['K10e.  Food provided, then not provided', ''],
      ['K10f.  Rent charged, then not charged', ''],
      ['K10g.  Low season instead of a normal month', '']],
     widths=[9.0, 7.2])

doc.save(OUT)
print('saved', OUT)
