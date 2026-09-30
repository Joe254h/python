# -*- coding: utf-8 -*-
"""Compare two builds: paragraph text, and where bold and italic sit."""
import docx, re, sys, difflib
from docx.oxml.ns import qn

def load(p):
    d = docx.Document(p)
    out = []
    for el in list(d.element.body):
        if el.tag != qn('w:p'):
            out.append(('[TABLE]', ''))
            continue
        pr = el.find(qn('w:pPr'))
        st = pr.find(qn('w:pStyle')) if pr is not None else None
        sty = (st.get(qn('w:val')) or '') if st is not None else ''
        marks = []
        for r in el.findall(qn('w:r')):
            t = ''.join(x.text or '' for x in r.findall(qn('w:t')))
            if not t.strip():
                continue
            rp = r.find(qn('w:rPr'))
            def on(tag):
                if rp is None: return False
                e = rp.find(qn(tag))
                if e is None: return False
                return (e.get(qn('w:val')) or 'true') not in ('0', 'false', 'off')
            b, i = on('w:b'), on('w:i')
            marks.append(('B' if b else '') + ('I' if i else '') or '-')
        txt = re.sub(r'\s+', ' ', ''.join(
            x.text or '' for x in el.iter(qn('w:t')))).strip()
        out.append((txt, f'{sty}|{",".join(marks)}'))
    return out

A, B = load(sys.argv[1]), load(sys.argv[2])
ta, tb = [x[0] for x in A], [x[0] for x in B]
sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
print('=== TEXT DIFFERENCES ===')
n = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        continue
    n += 1
    if n > 40: print('   …'); break
    for k in range(i1, i2): print(f'  - [{A[k][1]}] {A[k][0][:120]}')
    for k in range(j1, j2): print(f'  + [{B[k][1]}] {B[k][0][:120]}')
print(f'text-differing blocks: {sum(1 for t,_,_,_,_ in sm.get_opcodes() if t != "equal")}')

print('\n=== FORMATTING DIFFERENCES ON IDENTICAL TEXT ===')
m = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != 'equal':
        continue
    for k in range(i2 - i1):
        if A[i1 + k][1] != B[j1 + k][1]:
            m += 1
            if m <= 40:
                print(f'  {A[i1+k][0][:74]}')
                print(f'      was {A[i1+k][1]}')
                print(f'      now {B[j1+k][1]}')
print(f'formatting-differing paragraphs: {m}')
