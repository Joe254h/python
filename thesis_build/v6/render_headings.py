# -*- coding: utf-8 -*-
"""Work out what Word will actually paint for every heading.

Resolves each paragraph's numbering through the style chain (a paragraph's own
numPr, then its style's, then that style's basedOn), looks the list up in
numbering.xml, runs the level counters in document order and prints the text as
it will render. This is what a text-level check cannot see.
"""
import zipfile, re, sys
from lxml import etree

DOC = sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
z = zipfile.ZipFile(DOC)
doc = etree.fromstring(z.read('word/document.xml'))
styles = etree.fromstring(z.read('word/styles.xml'))
try:
    numbering = etree.fromstring(z.read('word/numbering.xml'))
except KeyError:
    numbering = None

STY = {s.get(W + 'styleId'): s for s in styles.findall(W + 'style')}

def style_num(sid, depth=0):
    """(numId, ilvl) inherited from a style, following basedOn."""
    if depth > 8 or sid not in STY: return None
    st = STY[sid]
    pPr = st.find(W + 'pPr')
    if pPr is not None:
        np = pPr.find(W + 'numPr')
        if np is not None:
            nid = np.find(W + 'numId'); lvl = np.find(W + 'ilvl')
            if nid is not None:
                return (nid.get(W + 'val'),
                        int(lvl.get(W + 'val')) if lvl is not None else 0)
    bo = st.find(W + 'basedOn')
    return style_num(bo.get(W + 'val'), depth + 1) if bo is not None else None

ABS = {}
if numbering is not None:
    num2abs = {n.get(W + 'numId'): n.find(W + 'abstractNumId').get(W + 'val')
               for n in numbering.findall(W + 'num')
               if n.find(W + 'abstractNumId') is not None}
    for an in numbering.findall(W + 'abstractNum'):
        lv = {}
        for l in an.findall(W + 'lvl'):
            t = l.find(W + 'lvlText'); s = l.find(W + 'start')
            f = l.find(W + 'numFmt')
            lv[int(l.get(W + 'ilvl'))] = (
                t.get(W + 'val') if t is not None else '',
                int(s.get(W + 'val')) if s is not None else 1,
                f.get(W + 'val') if f is not None else 'decimal')
        ABS[an.get(W + 'abstractNumId')] = lv

counters = {}
def paint(numId, ilvl):
    a = num2abs.get(numId)
    if a is None or a not in ABS or ilvl not in ABS[a]: return ''
    text, start, fmt = ABS[a][ilvl]
    if fmt == 'none': return ''
    c = counters.setdefault(a, {})
    c[ilvl] = c.get(ilvl, start - 1) + 1
    for deeper in [k for k in c if k > ilvl]: del c[deeper]
    out = text
    for lv in range(ilvl + 1):
        val = c.get(lv, ABS[a].get(lv, ('', 1, ''))[1])
        out = out.replace(f'%{lv+1}', str(val))
    return out + ' '

def ptx(p): return ''.join(t.text or '' for t in p.iter(W + 't')).strip()

rows = []
for p in doc.iter(W + 'p'):
    pPr = p.find(W + 'pPr')
    sid = ''
    npr = None
    if pPr is not None:
        ps = pPr.find(W + 'pStyle')
        sid = ps.get(W + 'val') if ps is not None else ''
        np = pPr.find(W + 'numPr')
        if np is not None:
            nid = np.find(W + 'numId'); lvl = np.find(W + 'ilvl')
            if nid is not None and nid.get(W + 'val') != '0':
                npr = (nid.get(W + 'val'),
                       int(lvl.get(W + 'val')) if lvl is not None else 0)
    if npr is None and sid:
        npr = style_num(sid)
    txt = ptx(p)
    if not txt: continue
    pre = paint(*npr) if npr else ''
    if re.fullmatch(r'Heading[1-9]', sid or '') or txt.upper().startswith('CHAPTER'):
        rows.append((sid or 'Normal', pre, txt))

print(f'{len(rows)} headings, as Word will render them:\n')
# Every chapter and section number in this thesis is typed into the text, so
# any prefix Word paints on a heading is a duplicate.
bad = 0
for sid, pre, txt in rows:
    flag = ''
    if pre.strip():
        flag = f'   <-- Word paints {pre.strip()!r} in front'; bad += 1
    print(f'  [{sid:9s}] {(pre + txt)[:78]}{flag}')
print(f'\nheadings rendering with an unwanted painted number: {bad}')
sys.exit(1 if bad else 0)
