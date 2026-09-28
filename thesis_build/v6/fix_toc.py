# -*- coding: utf-8 -*-
"""Rebuild the table of contents from the headings that are actually in the
document.  The old field result still carried draft 10's numbering, so the
entries are written out as text with PAGEREF fields; pressing F9 in Word fills
in the page numbers without disturbing the wording."""
import docx, re
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)
body = d.element.body
FONT, SZ = 'Times New Roman', '24'

def ptx(el):
    return ''.join(n.text or '' for n in el.iter(qn('w:t'))).strip()

def run(text, *, bold=False):
    r = OxmlElement('w:r'); rPr = OxmlElement('w:rPr')
    rf = OxmlElement('w:rFonts')
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'): rf.set(qn(a), FONT)
    rPr.append(rf)
    if bold: rPr.append(OxmlElement('w:b'))
    for tag in ('w:sz', 'w:szCs'):
        e = OxmlElement(tag); e.set(qn('w:val'), SZ); rPr.append(e)
    c = OxmlElement('w:color'); c.set(qn('w:val'), '000000'); rPr.append(c)
    r.append(rPr)
    t = OxmlElement('w:t'); t.set(qn('xml:space'), 'preserve'); t.text = text
    r.append(t)
    return r

def entry(text, name, *, bold=False, indent=0):
    p = OxmlElement('w:p'); pPr = OxmlElement('w:pPr')
    tt = OxmlElement('w:tabs')
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right'); tab.set(qn('w:leader'), 'dot'); tab.set(qn('w:pos'), '8827')
    tt.append(tab); pPr.append(tt)
    sp = OxmlElement('w:spacing')
    sp.set(qn('w:line'), '276'); sp.set(qn('w:lineRule'), 'auto'); sp.set(qn('w:after'), '40')
    pPr.append(sp)
    if indent:
        ind = OxmlElement('w:ind'); ind.set(qn('w:left'), str(indent)); pPr.append(ind)
    p.append(pPr)
    p.append(run(text, bold=bold))
    tr = OxmlElement('w:r'); tr.append(OxmlElement('w:tab')); p.append(tr)
    for r in pageref(name): p.append(r)
    return p

def pageref(name):
    out = []
    b = OxmlElement('w:r'); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), 'begin'); b.append(f); out.append(b)
    i = OxmlElement('w:r'); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve')
    it.text = f' PAGEREF {name} \\h '; i.append(it); out.append(i)
    s = OxmlElement('w:r'); f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'separate'); s.append(f2); out.append(s)
    out.append(run('  '))
    e = OxmlElement('w:r'); f3 = OxmlElement('w:fldChar'); f3.set(qn('w:fldCharType'), 'end'); e.append(f3); out.append(e)
    return out

# Close any bookmark the source document left open. An unmatched bookmarkStart
# is what Word reports as a damaged cross-reference.
_starts = {}
for _b in body.iter(qn('w:bookmarkStart')):
    _starts.setdefault(_b.get(qn('w:id')), []).append(_b)
_ends = {_b.get(qn('w:id')) for _b in body.iter(qn('w:bookmarkEnd'))}
_orphans = 0
for _id, _els in _starts.items():
    if _id in _ends: continue
    _el = _els[-1]
    _be = OxmlElement('w:bookmarkEnd'); _be.set(qn('w:id'), _id)
    _p = _el.getparent()
    _p.append(_be) if _p.tag == qn('w:p') else _el.addnext(_be)
    _orphans += 1
if _orphans:
    print(f'unclosed bookmarks from the source document closed: {_orphans}')

_bid = [52000]
# drop any bookmarks this script left behind on an earlier run
for bs in list(body.iter(qn('w:bookmarkStart'))):
    if (bs.get(qn('w:name')) or '').startswith('_Toc_'):
        bid = bs.get(qn('w:id'))
        for be in list(body.iter(qn('w:bookmarkEnd'))):
            if be.get(qn('w:id')) == bid: be.getparent().remove(be)
        bs.getparent().remove(bs)

def bookmark(el, name):
    _bid[0] += 1
    bs = OxmlElement('w:bookmarkStart'); bs.set(qn('w:id'), str(_bid[0])); bs.set(qn('w:name'), name)
    be = OxmlElement('w:bookmarkEnd');   be.set(qn('w:id'), str(_bid[0]))
    el.insert(0 if el.find(qn('w:pPr')) is None else 1, bs)
    el.append(be)

# ------------------------------------------------------- 1. collect headings
FRONT_BEFORE = ['DECLARATION', 'DEDICATION', 'ACKNOWLEDGEMENT', 'ABSTRACT']
FRONT_AFTER  = ['LIST OF TABLES', 'LIST OF FIGURES', 'LIST OF ABBREVIATIONS']
TAIL         = ['REFERENCES', 'APPENDICES']
SEC = re.compile(r'^(\d+)\.(\d+)(?:\.(\d+))?\s')

kids = list(body)
toc_i = next(i for i, el in enumerate(kids)
             if el.tag == qn('w:p') and ptx(el).upper() == 'TABLE OF CONTENTS')

# The stale contents rows repeat the front-matter and chapter labels. Bookmarking
# one of those rows and then deleting it is what left three PAGEREF fields
# pointing at nothing, so headings are collected only from after the contents.
stop_at = {'LIST OF TABLES', 'LIST OF FIGURES', 'LIST OF ABBREVIATIONS',
           'CHAPTER ONE: INTRODUCTION'}
_j = toc_i + 1
while _j < len(kids):
    if kids[_j].tag == qn('w:p') and ptx(kids[_j]).upper() in stop_at: break
    _j += 1
assert _j < len(kids), 'end of the stale contents list not found'
body_start = _j

items = []          # (text, bookmark, level)
seen = set()
k = 0
for i, el in enumerate(kids):
    if i < body_start: continue
    if el.tag != qn('w:p'): continue
    t = ptx(el)
    if not t or len(t) > 130: continue
    lvl = None
    if t.upper() in FRONT_BEFORE + FRONT_AFTER + TAIL and t.upper() not in seen:
        seen.add(t.upper()); lvl = 0
    elif t.startswith('CHAPTER ') and re.match(r'^CHAPTER (ONE|TWO|THREE|FOUR|FIVE|SIX)\b', t):
        lvl = 0
    else:
        m = SEC.match(t)
        sty = ''
        pPr = el.find(qn('w:pPr'))
        if pPr is not None:
            ps = pPr.find(qn('w:pStyle'))
            if ps is not None: sty = ps.get(qn('w:val')) or ''
        if m and sty.lower().startswith('heading'):
            lvl = 2 if m.group(3) else 1
    if lvl is None: continue
    k += 1
    name = f'_Toc_{k}'
    bookmark(el, name)
    items.append((t, name, lvl))

# ------------------------------------------- 2. clear the stale field result
kids = list(body)
toc_i = next(i for i, el in enumerate(kids)
             if el.tag == qn('w:p') and ptx(el).upper() == 'TABLE OF CONTENTS')
j = toc_i + 1
while j < len(kids):
    el = kids[j]
    if el.tag == qn('w:p') and ptx(el).upper() in stop_at: break
    j += 1
assert j < len(kids), 'end of the old contents list not found'
anchor = kids[j]
removed = 0
for el in kids[toc_i + 1:j]:
    body.remove(el); removed += 1

# ------------------------------------------------------- 3. write the entries
for text, name, lvl in items:
    anchor.addprevious(entry(text, name, bold=(lvl == 0), indent=lvl * 360))

d.save(DOC)
print(f'contents rebuilt: {removed} stale rows removed, {len(items)} written '
      f'({sum(1 for _,_,l in items if l==0)} level-0, '
      f'{sum(1 for _,_,l in items if l==1)} level-1, '
      f'{sum(1 for _,_,l in items if l==2)} level-2)')
