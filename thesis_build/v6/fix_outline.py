# -*- coding: utf-8 -*-
"""Give every front-matter heading and every chapter/section heading an outline
level so Word's TOC field picks it up when the reader presses F9."""
import docx, re
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)

FRONT = {'DECLARATION', 'DEDICATION', 'ACKNOWLEDGEMENT', 'ABSTRACT',
         'LIST OF TABLES', 'LIST OF FIGURES', 'LIST OF ABBREVIATIONS',
         'REFERENCES', 'APPENDICES'}
SEC = re.compile(r'^(\d+)\.(\d+)(\.(\d+))?\s')

def set_outline(p, lvl):
    pPr = p._p.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr'); p._p.insert(0, pPr)
    for old in pPr.findall(qn('w:outlineLvl')):
        pPr.remove(old)
    e = OxmlElement('w:outlineLvl'); e.set(qn('w:val'), str(lvl))
    # outlineLvl belongs after numPr/spacing but before rPr
    rPr = pPr.find(qn('w:rPr'))
    if rPr is not None: rPr.addprevious(e)
    else: pPr.append(e)
    return True

n = {0: 0, 1: 0, 2: 0}
for p in d.paragraphs:
    t = p.text.strip()
    if not t or len(t) > 130:
        continue
    if t in FRONT or t.startswith('CHAPTER '):
        set_outline(p, 0); n[0] += 1
        continue
    m = SEC.match(t)
    if m and p.style.name.startswith('Heading'):
        lvl = 2 if m.group(4) else 1
        set_outline(p, lvl); n[lvl] += 1

d.save(DOC)
print('outline levels set — level 0:', n[0], ' level 1:', n[1], ' level 2:', n[2])
