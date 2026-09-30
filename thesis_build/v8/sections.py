# -*- coding: utf-8 -*-
"""Word count by region, on the boundaries the university counts."""
import docx, re, sys
from docx.oxml.ns import qn

path = sys.argv[1]
d = docx.Document(path)
els = [el for el in list(d.element.body)]
def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))
def wc(t): return len([w for w in re.split(r'\s+', t.strip()) if w])
def style(el):
    pr = el.find(qn('w:pPr'))
    st = pr.find(qn('w:pStyle')) if pr is not None else None
    return (st.get(qn('w:val')) or '') if st is not None else ''

# region boundaries, by the last occurrence of each front-matter marker
def mark(name, which=-1):
    hits = [i for i, el in enumerate(els)
            if el.tag == qn('w:p') and txt(el).strip().upper() == name]
    return hits[which] if hits else None

toc   = mark('TABLE OF CONTENTS', 0)
lot   = mark('LIST OF TABLES')
lof   = mark('LIST OF FIGURES')
labb  = mark('LIST OF ABBREVIATIONS')
ch1   = next(i for i, el in enumerate(els)
             if el.tag == qn('w:p') and style(el).startswith('Heading')
             and txt(el).strip().upper().startswith('CHAPTER ONE'))
refs  = mark('REFERENCES')
apx   = mark('APPENDICES')

def block(a, b, label):
    p = t = 0
    for el in els[a:b]:
        if el.tag == qn('w:p'): p += wc(txt(el))
        elif el.tag == qn('w:tbl'): t += wc(txt(el))
    print(f'  {label:44s} paragraphs {p:6,}   tables {t:5,}')
    return p, t

print(path)
fm, _   = block(0, toc, 'title page to abstract')
tocw, _ = block(toc, lot, 'table of contents')
lotw, _ = block(lot, lof, 'list of tables')
lofw, _ = block(lof, labb, 'list of figures')
abbw, _ = block(labb, ch1, 'list of abbreviations')
bodyp, bodyt = block(ch1, refs, 'CHAPTERS ONE TO SIX')
refw, _ = block(refs, apx, 'references')
apxp, apxt = block(apx, len(els), 'appendices')

# Word counts text inside tables, so the figure to watch adds them in
target = bodyp + bodyt + tocw + lotw + lofw
print()
print(f'  Ch 1-6 (prose + tables) + contents + list of tables + list of figures = {target:,}')
print(f'  the same without table text                                      = '
      f'{bodyp + tocw + lotw + lofw:,}')
# Word counts each page number in the contents and the two lists as a word
# once the fields are updated, so add one per row
rows = sum(1 for el in els[toc:ch1]
           if el.tag == qn('w:p') and wc(txt(el)) and txt(el).strip().upper() not in
           ('TABLE OF CONTENTS', 'LIST OF TABLES', 'LIST OF FIGURES', 'LIST OF ABBREVIATIONS'))
print(f'  plus one page number per contents / list row              + {rows:,}')
print(f'  what Word will show after Ctrl+A F9                       = {target + rows:,}')
t2 = target + rows
print(f'  target 29,000  ->  {"under by " + format(29000 - t2, ",") if t2 <= 29000 else "OVER by " + format(t2 - 29000, ",")}')
print(f'  whole document, paragraphs only                                  = '
      f'{fm + tocw + lotw + lofw + abbw + bodyp + refw + apxp:,}')
