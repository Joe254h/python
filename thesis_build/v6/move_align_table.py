# -*- coding: utf-8 -*-
"""The objectives-to-analysis table was sitting inside the table of contents in
the source document. Move it into section 3.9 where it belongs, give it the
APA caption Table 1 and drop the note, whose content is already in the section
text."""
import docx, re
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)
body = d.element.body
kids = list(body)
def ptx(el): return ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip()

# ---- locate the stray block: caption, title, table, note
ti = None
for i, e in enumerate(kids):
    if e.tag == qn('w:tbl') and 'Variables measured' in ptx(e):
        ti = i; break
if ti is None:
    print('alignment table not found — nothing to move'); raise SystemExit
block = [kids[ti]]
# caption paragraphs immediately above
j = ti - 1
while j >= 0 and kids[j].tag == qn('w:p') and (
        ptx(kids[j]).startswith('Table 3.1') or
        ptx(kids[j]).startswith('Alignment of Study Objectives')):
    block.insert(0, kids[j]); j -= 1
# the note immediately below
k = ti + 1
if k < len(kids) and kids[k].tag == qn('w:p') and ptx(kids[k]).startswith('Note.'):
    note = kids[k]
else:
    note = None

# ---- find section 3.9 in the body (the heading, not the contents row)
anchor = None
for i, e in enumerate(kids):
    if e.tag != qn('w:p'): continue
    t = ptx(e)
    if t == '3.10 Data analysis' and i > ti:
        anchor = e; break
assert anchor is not None, 'section 3.10 heading not found in the body'

for el in block: body.remove(el)
if note is not None: body.remove(note)
for el in block: anchor.addprevious(el)

# ---- APA caption: "Table 1" on its own line, italic title beneath
FONT, SZ = 'Times New Roman', '24'
def run(text, *, bold=False, italic=False):
    r = OxmlElement('w:r'); rPr = OxmlElement('w:rPr')
    rf = OxmlElement('w:rFonts')
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'): rf.set(qn(a), FONT)
    rPr.append(rf)
    if bold: rPr.append(OxmlElement('w:b'))
    if italic: rPr.append(OxmlElement('w:i'))
    for tag in ('w:sz', 'w:szCs'):
        e = OxmlElement(tag); e.set(qn('w:val'), SZ); rPr.append(e)
    c = OxmlElement('w:color'); c.set(qn('w:val'), '000000'); rPr.append(c)
    r.append(rPr)
    t = OxmlElement('w:t'); t.set(qn('xml:space'), 'preserve'); t.text = text
    r.append(t)
    return r

def setpara(p, text, *, bold=False, italic=False):
    for child in p.findall(qn('w:r')) + p.findall(qn('w:hyperlink')):
        p.remove(child)
    p.append(run(text, bold=bold, italic=italic))

caps = [el for el in block if el.tag == qn('w:p')]
if len(caps) >= 2:
    setpara(caps[0], 'Table 1', bold=True)
    setpara(caps[1], 'Alignment of Study Objectives, Variables Measured and Analysis Applied',
            italic=True)
elif len(caps) == 1:
    setpara(caps[0], 'Table 1', bold=True)
    tp = OxmlElement('w:p')
    tp.append(run('Alignment of Study Objectives, Variables Measured and Analysis Applied',
                  italic=True))
    caps[0].addnext(tp)

d.save(DOC)
print('alignment table moved into section 3.9 and captioned Table 1;',
      'note removed' if note is not None else 'no note found')
