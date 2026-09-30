# -*- coding: utf-8 -*-
"""Where the words are, counted the way Word appears to count them.

Word reported 35,908 for this document. Counting every paragraph, counting the
paragraphs inside table cells one at a time, treating a cell such as
"25 (38.5%)" as a single token and adding one page number per contents row
lands within a few hundred of that, which is close enough to allocate a cut.
"""
import docx, re, sys
from docx.oxml.ns import qn

path = sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx'
d = docx.Document(path)
els = list(d.element.body)
NP = re.compile(r'^[\d,]+(\.\d+)? \([\d.]+%\)$')

def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))
def wc(t):
    t = t.strip()
    if NP.match(t):
        return 1
    return len([w for w in re.split(r'\s+', t) if w])

def size(el):
    if el.tag == qn('w:p'):
        n = wc(txt(el))
        if any(f.text and 'PAGEREF' in f.text for f in el.iter(qn('w:instrText'))):
            n += 1
        return n
    if el.tag == qn('w:tbl'):
        return sum(wc(txt(p)) for p in el.iter(qn('w:p')))
    return 0

def mark(name, which=-1):
    hits = [i for i, el in enumerate(els)
            if el.tag == qn('w:p') and txt(el).strip().upper() == name]
    return hits[which] if hits else None

toc = mark('TABLE OF CONTENTS', 0)
lot = mark('LIST OF TABLES')
lof = mark('LIST OF FIGURES')
lab = mark('LIST OF ABBREVIATIONS')
ch1 = next(i for i, el in enumerate(els)
           if el.tag == qn('w:p') and (el.find(qn('w:pPr')) is not None)
           and (el.find(qn('w:pPr')).find(qn('w:pStyle')) is not None)
           and (el.find(qn('w:pPr')).find(qn('w:pStyle')).get(qn('w:val')) or '').startswith('Heading')
           and txt(el).strip().upper().startswith('CHAPTER ONE'))
refs = mark('REFERENCES')
apx = mark('APPENDICES')

chapters = []
for name in ('CHAPTER ONE', 'CHAPTER TWO', 'CHAPTER THREE', 'CHAPTER FOUR',
             'CHAPTER FIVE', 'CHAPTER SIX'):
    chapters.append(next(i for i, el in enumerate(els)
                         if el.tag == qn('w:p') and txt(el).strip().upper().startswith(name)
                         and i >= ch1))

def block(a, b, label):
    n = sum(size(el) for el in els[a:b])
    print(f'  {label:36s} {n:7,}')
    return n

print(path)
tot = 0
tot += block(0, toc, 'title page, declaration, abstract')
tot += block(toc, lot, 'table of contents')
tot += block(lot, lof, 'list of tables')
tot += block(lof, lab, 'list of figures')
tot += block(lab, ch1, 'list of abbreviations')
print('  ' + '-' * 44)
for k, i in enumerate(chapters):
    j = chapters[k + 1] if k + 1 < len(chapters) else refs
    tot += block(i, j, ['Chapter One', 'Chapter Two', 'Chapter Three',
                        'Chapter Four', 'Chapter Five', 'Chapter Six'][k])
print('  ' + '-' * 44)
tot += block(refs, apx, 'references')
tot += block(apx, len(els), 'appendix: the questionnaire')
print('  ' + '=' * 44)
print(f'  {"TOTAL":36s} {tot:7,}')
print(f'  {"target":36s} {29000:7,}   -> cut {tot - 29000:,}' if tot > 29000
      else f'  under target by {29000 - tot:,}')
