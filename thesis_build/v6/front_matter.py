# -*- coding: utf-8 -*-
"""Rebuild LIST OF TABLES / LIST OF FIGURES from the actual captions, bookmark
every caption, and convert the four Chapter 1-3 figure captions to APA 7
(number line + italic title line, placed above the image)."""
import docx, re, copy
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)
body = d.element.body

def ptx(el):
    return ''.join(n.text or '' for n in el.iter(qn('w:t'))).strip()

def has_img(el):
    return el.find('.//' + qn('a:blip')) is not None

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

def para(*runs, align=None, tabs=None, spacing=None):
    p = OxmlElement('w:p'); pPr = OxmlElement('w:pPr')
    if tabs:
        tt = OxmlElement('w:tabs')
        for pos, leader in tabs:
            tab = OxmlElement('w:tab')
            tab.set(qn('w:val'), 'right'); tab.set(qn('w:leader'), leader)
            tab.set(qn('w:pos'), str(pos)); tt.append(tab)
        pPr.append(tt)
    sp = OxmlElement('w:spacing')
    sp.set(qn('w:line'), str(spacing or 276)); sp.set(qn('w:lineRule'), 'auto')
    sp.set(qn('w:after'), '60'); pPr.append(sp)
    if align:
        j = OxmlElement('w:jc'); j.set(qn('w:val'), align); pPr.append(j)
    p.append(pPr)
    for r in runs: p.append(r)
    return p

_bid = [41000]
def clear_old_bookmarks():
    """Remove bookmarks a previous run of this script inserted, so ids stay unique."""
    seen = set()
    for bs in list(body.iter(qn('w:bookmarkStart'))):
        nm = bs.get(qn('w:name')) or ''
        bid = bs.get(qn('w:id'))
        if nm.startswith(('_Tbl', '_Fig')) or bid in seen:
            for be in list(body.iter(qn('w:bookmarkEnd'))):
                if be.get(qn('w:id')) == bid:
                    be.getparent().remove(be)
            bs.getparent().remove(bs)
        seen.add(bid)

clear_old_bookmarks()

def bookmark(p, name):
    _bid[0] += 1
    bs = OxmlElement('w:bookmarkStart'); bs.set(qn('w:id'), str(_bid[0])); bs.set(qn('w:name'), name)
    be = OxmlElement('w:bookmarkEnd');   be.set(qn('w:id'), str(_bid[0]))
    p.insert(0 if p.find(qn('w:pPr')) is None else 1, bs)
    p.append(be)

def pageref(name):
    """PAGEREF field; cached result is blank until the reader presses F9."""
    out = []
    b = OxmlElement('w:r'); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), 'begin'); b.append(f); out.append(b)
    i = OxmlElement('w:r'); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve')
    it.text = f' PAGEREF {name} \\h '; i.append(it); out.append(i)
    s = OxmlElement('w:r'); f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'separate'); s.append(f2); out.append(s)
    out.append(run('  '))
    e = OxmlElement('w:r'); f3 = OxmlElement('w:fldChar'); f3.set(qn('w:fldCharType'), 'end'); e.append(f3); out.append(e)
    return out

# ---------------------------------------------------------------------------
# 1. Chapter 1-3 figures: caption below -> APA 7 number + italic title above
# ---------------------------------------------------------------------------
kids = list(body)
ch13 = []
for i, el in enumerate(kids):
    if el.tag == qn('w:p') and has_img(el):
        nxt = kids[i + 1] if i + 1 < len(kids) else None
        prv = kids[i - 1] if i >= 1 else None
        # The title must be separated from the number, otherwise "Figure 23"
        # backtracks to number 2 with title "3" and a Chapter Four caption is
        # rewritten as a Chapter One to Three one.
        m = re.match(r'^Figure\s*(\d+)\s*[:.]?\s+(\S.*)$',
                     ptx(nxt) if nxt is not None else '')
        if m and int(m.group(1)) <= 4:
            ch13.append((el, nxt, int(m.group(1)), m.group(2).strip()))
print('Chapter 1-3 figure captions found:', [(n, t[:45]) for _, _, n, t in ch13])

for img_p, cap_p, num, title in ch13:
    numP = para(run(f'Figure {num}', bold=True), spacing=240)
    titP = para(run(title, italic=True), spacing=240)
    img_p.addprevious(numP); img_p.addprevious(titP)
    body.remove(cap_p)
    pPr = img_p.find(qn('w:pPr'))
    if pPr is None:
        pPr = OxmlElement('w:pPr'); img_p.insert(0, pPr)
    for j in pPr.findall(qn('w:jc')): pPr.remove(j)
    jc = OxmlElement('w:jc'); jc.set(qn('w:val'), 'center')
    tail = pPr.find(qn('w:rPr'))
    if tail is None: tail = pPr.find(qn('w:sectPr'))
    if tail is not None: tail.addprevious(jc)
    else: pPr.append(jc)

# ---------------------------------------------------------------------------
# 2. bookmark every Chapter 4-6 caption and harvest its title
# ---------------------------------------------------------------------------
kids = list(body)
tables, figures = [], []
for i, el in enumerate(kids):
    if el.tag != qn('w:p'): continue
    t = ptx(el)
    m = re.fullmatch(r'(Table|Figure)\s+(\d+)', t)
    if not m: continue
    kind, num = m.group(1), int(m.group(2))
    title = ptx(kids[i + 1]) if i + 1 < len(kids) else ''
    if not title or re.fullmatch(r'(Table|Figure)\s+\d+', title): continue
    name = f'_{"Tbl" if kind == "Table" else "Fig"}{num}'
    bookmark(el, name)
    (tables if kind == 'Table' else figures).append((num, title, name))
figures.sort()
tables.sort()
print(f'captions bookmarked: {len(tables)} tables, {len(figures)} figures')
assert [n for n, _, _ in tables] == list(range(1, len(tables) + 1)), [n for n,_,_ in tables]
assert [n for n, _, _ in figures] == list(range(1, len(figures) + 1)), [n for n,_,_ in figures]

# ---------------------------------------------------------------------------
# 3. rebuild the two lists
# ---------------------------------------------------------------------------
def rebuild(heading, items, label):
    kids = list(body)
    hi = next(i for i, el in enumerate(kids)
              if el.tag == qn('w:p') and ptx(el).upper() == heading)
    j = hi + 1
    while j < len(kids) and kids[j].tag == qn('w:p') and re.match(
            r'^(Table|Figure)\s*\d+', ptx(kids[j])):
        j += 1
    anchor = kids[j]
    for el in kids[hi + 1:j]:
        body.remove(el)
    for num, title, name in items:
        p = para(run(f'{label} {num}: {title}'), tabs=[(8827, 'dot')])
        tab_r = OxmlElement('w:r'); tb = OxmlElement('w:tab'); tab_r.append(tb)
        p.append(tab_r)
        for r in pageref(name): p.append(r)
        anchor.addprevious(p)
    print(f'{heading}: {len(items)} entries written')

rebuild('LIST OF TABLES', tables, 'Table')
rebuild('LIST OF FIGURES', figures, 'Figure')

d.save(DOC)
print('saved', DOC)
