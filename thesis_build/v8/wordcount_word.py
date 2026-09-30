# -*- coding: utf-8 -*-
"""Count the way Word counts.

Word counts every paragraph in the document, including the paragraphs inside
table cells, and it counts the result of a field such as a page number as a
word. Joining a whole table's text before splitting merges the last token of
one cell with the first of the next, which undercounts; this counts cell by
cell.
"""
import docx, re, sys
from docx.oxml.ns import qn

path = sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx'
d = docx.Document(path)
body = d.element.body

def wc(t): return len([w for w in re.split(r'\s+', t.strip()) if w])
def ptext(p): return ''.join(t.text or '' for t in p.iter(qn('w:t')))

def count(el):
    """Words in one body-level element, paragraph by paragraph."""
    if el.tag == qn('w:p'):
        return wc(ptext(el)), 0
    if el.tag == qn('w:tbl'):
        return 0, sum(wc(ptext(p)) for p in el.iter(qn('w:p')))
    return 0, 0

para = tbl = 0
for el in list(body):
    a, b = count(el)
    para += a; tbl += b

# page numbers that appear once the fields are updated
fields = 0
for el in list(body):
    if el.tag != qn('w:p'):
        continue
    if any(f.text and 'PAGEREF' in f.text for f in el.iter(qn('w:instrText'))):
        fields += 1

print(f'{path}')
print(f'  paragraph words                 : {para:,}')
print(f'  words inside tables (cell by cell): {tbl:,}')
print(f'  page numbers once fields update : {fields:,}')
print(f'  WHAT WORD SHOWS                 : {para + tbl + fields:,}')
