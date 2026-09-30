# -*- coding: utf-8 -*-
"""Where is bold used, and does the style chain add any?"""
import docx, re, sys
from docx.oxml.ns import qn

d = docx.Document(sys.argv[1])
els = list(d.element.body)
def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))

# 1. styles that turn bold on
print('--- styles whose definition sets bold ---')
for st in d.styles.element.findall(qn('w:style')):
    rpr = st.find(qn('w:rPr'))
    name = st.find(qn('w:name'))
    sid = st.get(qn('w:styleId'))
    if rpr is not None and rpr.find(qn('w:b')) is not None:
        b = rpr.find(qn('w:b'))
        v = b.get(qn('w:val'))
        print(f'   {sid:22s} {name.get(qn("w:val")) if name is not None else "":26s} w:val={v!r}')

# 2. direct bold runs, in the body
print('\n--- paragraphs with a directly bold run ---')
n = 0
for el in els:
    if el.tag != qn('w:p'):
        continue
    hits = []
    for r in el.findall(qn('w:r')):
        t = ''.join(x.text or '' for x in r.findall(qn('w:t')))
        rp = r.find(qn('w:rPr'))
        if rp is not None and rp.find(qn('w:b')) is not None:
            bv = rp.find(qn('w:b')).get(qn('w:val'))
            if bv not in ('0', 'false'):
                hits.append(t)
    if hits:
        n += 1
        if n <= 40:
            flat = re.sub(r'\s+', ' ', txt(el))[:70]
            print(f'   {flat:72s} bold runs: {[h[:34] for h in hits]}')
print(f'paragraphs with direct bold: {n}')

# 3. inside tables
n2 = 0
for el in els:
    if el.tag != qn('w:tbl'):
        continue
    for r in el.iter(qn('w:r')):
        rp = r.find(qn('w:rPr'))
        if rp is not None and rp.find(qn('w:b')) is not None:
            if rp.find(qn('w:b')).get(qn('w:val')) not in ('0', 'false'):
                n2 += 1
print(f'bold runs inside tables: {n2}')
