# -*- coding: utf-8 -*-
"""Make the questionnaire safe for full collection:
   1. kill the duplicate B25-B28 by aligning the catchment block to Kobo's B31-B34
   2. fix the B27a cross-reference
   3. restore interview timing capture
   4. add a first-day data check (the substitute for the re-test that was declined)
   5. annex the Word <-> Kobo variable map, since the data carries Kobo's names
"""
import re, json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

SRC=('/root/.claude/uploads/920ad5d8-6e07-5909-9e17-40c3ac0fe128/'
     'd1db90b2-Trader_Questionnaire_FULL_edited.docx')
OUT='/home/user/python/output/Trader_Questionnaire_FULL_v5_FIELD_READY.docx'
F='Calibri'; RED=RGBColor(0xC0,0,0); NAVY=RGBColor(0x1F,0x38,0x64)
STEEL=RGBColor(0x1F,0x4D,0x78); GREY=RGBColor(0x59,0x59,0x59); BLACK=RGBColor(0,0,0)
doc=Document(SRC); body=doc.element.body
cont=lambda b:[e for e in b if e.tag!=qn('w:sectPr')]

def run(p,t,size=11,bold=False,italic=False,color=BLACK):
    r=p.add_run(t); r.font.name=F; r.font.size=Pt(size)
    r.font.bold=bold; r.font.italic=italic; r.font.color.rgb=color
    rpr=r._element.get_or_add_rPr(); rf=rpr.find(qn('w:rFonts'))
    if rf is None: rf=OxmlElement('w:rFonts'); rpr.insert(0,rf)
    for a in ('w:ascii','w:hAnsi','w:cs','w:eastAsia'): rf.set(qn(a),F)
    return r
def para(t='',size=11,bold=False,italic=False,color=BLACK,before=0,after=4,indent=0):
    p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(before)
    p.paragraph_format.space_after=Pt(after)
    if indent: p.paragraph_format.left_indent=Cm(indent)
    if t: run(p,t,size,bold,italic,color)
    return p
def h1(t):
    p=para(t,size=15,bold=True,color=NAVY,before=16,after=8)
    pPr=p._p.get_or_add_pPr(); b=OxmlElement('w:pBdr'); bo=OxmlElement('w:bottom')
    bo.set(qn('w:val'),'single'); bo.set(qn('w:sz'),'6'); bo.set(qn('w:space'),'4'); bo.set(qn('w:color'),'1F3864')
    b.append(bo); pPr.append(b); return p
def h2(t,color=STEEL): return para(t,size=12.5,bold=True,color=color,before=12,after=5)
def q(num,text,codes=None,red=False):
    c = RED if red else BLACK
    p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(5); p.paragraph_format.space_after=Pt(1)
    p.paragraph_format.left_indent=Cm(1.05); p.paragraph_format.first_line_indent=Cm(-1.05)
    run(p,num+'  ',bold=True,color=c); run(p,text,color=c)
    if codes:
        cp=doc.add_paragraph(); cp.paragraph_format.left_indent=Cm(1.05)
        cp.paragraph_format.space_before=Pt(0); cp.paragraph_format.space_after=Pt(3)
        run(cp,codes,size=10.5,color=c)
    return p
def instr(t,red=False): return para(t,size=10,italic=True,color=RED if red else GREY,before=2,after=4,indent=1.05)
def shade(cell,hexv):
    tcPr=cell._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd')
    sh.set(qn('w:val'),'clear'); sh.set(qn('w:color'),'auto'); sh.set(qn('w:fill'),hexv); tcPr.append(sh)
def cell(c,t,bold=False,size=9,color=BLACK):
    c.text=''; p=c.paragraphs[0]; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(2)
    if t: run(p,t,size,bold,color=color)
def tbl(header,rows,widths,size=9):
    t=doc.add_table(rows=len(rows)+1,cols=len(header)); t.style='Table Grid'
    t.alignment=WD_TABLE_ALIGNMENT.LEFT; t.autofit=False
    for r in t.rows:
        for i,w in enumerate(widths): r.cells[i].width=Cm(w)
    for i,l in enumerate(header):
        cell(t.rows[0].cells[i],l,bold=True,size=9,color=RGBColor(0xFF,0xFF,0xFF)); shade(t.rows[0].cells[i],'1F4D78')
    for ri,row in enumerate(rows,1):
        for ci,v in enumerate(row): cell(t.rows[ri].cells[ci],v,bold=(ci==0),size=size)
    return t

# ---------- FIX 1+2: renumber the duplicated catchment block, fix cross-ref ----
RENUM={'B25.':'B31.','B26.':'B32.','B27.':'B33.','B28.':'B34.'}
CATCH=('Where do you live','How do you usually travel','How long does that journey',
       'Do you bring a child aged 0-3 with you on that journey')
fixed=[]
for p in doc.paragraphs:
    t=p.text.strip()
    m=re.match(r'^(B\d{1,2}[a-z]?\.)\s+(.*)$',t)
    if m and m.group(1) in RENUM and any(t2 in m.group(2) for t2 in CATCH):
        consumed=0; lab=m.group(1)
        for r in p.runs:
            if consumed>=len(lab): break
            if consumed==0 and r.text.startswith('B'):
                r.text=RENUM[lab][0]+RENUM[lab][1:len(r.text)] if len(r.text)>=len(lab) else r.text
                r.text=re.sub(r'^B\d{1,2}',RENUM[lab].rstrip('.'),r.text)
            r.font.color.rgb=RED; r.font.bold=True
            consumed+=len(r.text)
        fixed.append(RENUM[lab])
    if t.startswith('B27a.') and 'code from B23' in t:
        for r in p.runs:
            if 'B23' in r.text:
                r.text=r.text.replace('code from B23','code from B27'); r.font.color.rgb=RED
        fixed.append('B27a cross-ref')
print('renumbered / fixed:',fixed)

# ---------- FIX 3: restore interview timing, in Section K (Close) -------------
n0=len(cont(body))
q('K6.','Interview start time  ________ : ________   am / pm',red=True)
q('K7.','Interview end time  ________ : ________   am / pm',red=True)
instr('Added back. In the pilot, interview length was taken from when the tablet form was '
      'opened and closed. Three interviews then showed as over three hours and one as '
      'eighteen, because the form was left open. Interview length is one of our main quality '
      'checks, so it has to be recorded directly.',red=True)
new=cont(body)[n0:]
anchor=None
for p in doc.paragraphs:
    if p.text.strip().startswith('K5.'): anchor=p._p
if anchor is None:
    for p in doc.paragraphs:
        if p.text.strip().startswith('Section L'): anchor=p._p; break
    cur=None
    for el in new: body.remove(el); anchor.addprevious(el)
else:
    cur=anchor
    for el in new: body.remove(el); cur.addnext(el); cur=el
print('timing questions placed after', 'K5' if anchor is not None else 'end of K')

# ---------- FIX 4: first-day check, replacing the declined re-test ------------
n0=len(cont(body))
h2('F0f.  First-day check — replaces the DCE re-test',color=RED)
para('The re-test of the choice cards has been dropped. The one change we cannot verify from '
     'existing data is whether the tablet really is shuffling which option appears first. This '
     'check does the same job using the first day of real fieldwork, and costs nothing.',
     size=10.5,color=RED,after=5,indent=0.5)
tbl(['After the first…','Check','Expected','If it fails'],
 [['20 interviews','Count how often option A was shown first (the display-order field)',
   'Close to half — roughly 8 to 12 of 20',
   'STOP. The shuffle is not working. Do not continue until it is fixed.'],
  ['20 interviews','Count how many traders were flagged for choosing the same side every time',
   'A few at most','If more than 5 in 20, re-brief the enumerators on reading both options'],
  ['20 interviews','Check the block field holds 1, 2 or 3 and all three appear',
   'All three blocks present','Fix the assignment rule before continuing'],
  ['First day','Check recorded interview length (K6 to K7)','Mostly 35 to 55 minutes',
   'Investigate any interview under 20 minutes'],
  ['First day','Check every choice card was answered','No blanks',
   'Re-brief; blanks cannot be recovered later']],
 [2.6,5.4,3.4,4.8])
para('Whoever runs this check should report the four counts to the study team before day two '
     'begins. Twenty interviews is enough to see a broken shuffle; it is not enough to hide one.',
     size=10,italic=True,color=RED,after=6,indent=0.5)
new=cont(body)[n0:]
target=None
for p in doc.paragraphs:
    if p.text.strip().startswith('Block 1'): target=p._p; break
for el in new: body.remove(el); target.addprevious(el)
print('first-day check inserted before Block 1')

# ---------- FIX 5: annex the Word <-> Kobo variable map ----------------------
kobo=json.load(open('analysis/kobo_variables.json'))
n0=len(cont(body))
doc.add_page_break()
h1('Annex M — Variable names in the collected data')
para('IMPORTANT FOR ANALYSIS.',size=11,bold=True,color=RED,after=3)
para('This document and the tablet form number the questions differently. The data that comes '
     'out of the tablet carries the TABLET numbering, not the numbering in this document. '
     'Section B is where they diverge most: what this document calls B25 (lost trading days) '
     'is B27 in the data, and what the data calls B25 is net daily earnings. Anyone analysing '
     'the dataset must use the list below, not the numbering in the body of this document.',
     size=10.5,color=RED,after=6)
para('The tablet form is the operational instrument and has already collected pilot data under '
     'these names, so it has been left alone. This annex is the bridge.',size=10,italic=True,
     color=GREY,after=8)
h2('Section B as collected by the tablet')
rowsB=[(k,v[:78]) for k,v in kobo if re.match(r'^B\d',k)]
tbl(['Data field','Question'],rowsB,[2.6,13.6],size=8.5)
para('Sections A and C to J follow the tablet numbering too; the full list is in the Kobo form '
     'definition and in kobo_variables.json supplied with the analysis files.',size=10,
     italic=True,color=GREY,before=6)
new=cont(body)[n0:]
print('annex added,',len(rowsB),'section B fields listed')

doc.save(OUT); print('saved',OUT)
