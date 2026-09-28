# -*- coding: utf-8 -*-
"""Whole-thesis audit: citations against the reference list, the front-matter
lists against the captions, numbering, formatting and the reviewer's demands."""
import docx, re, collections
from docx.oxml.ns import qn
d = docx.Document('v6/thesis.docx')
body = d.element.body
kids = list(body)
def ptx(el): return ''.join(t.text or '' for t in el.iter(qn('w:t'))).strip()
paras = [ptx(e) for e in kids if e.tag == qn('w:p')]
full = '\n'.join(paras)

print('=' * 74)
print('1. REFERENCES')
# the first REFERENCES / APPENDICES hits are the table-of-contents rows
_rs = [i for i, p in enumerate(paras) if p == 'REFERENCES']
ri = _rs[-1]
ai = next((i for i, p in enumerate(paras[ri:], ri) if p == 'APPENDICES'), len(paras))
refs = [p for p in paras[ri+1:ai] if len(p) > 30]
print(f'   reference entries: {len(refs)}')
dups = [k for k, v in collections.Counter(refs).items() if v > 1]
print(f'   duplicate entries: {len(dups)}')
# author surnames that start each entry
keys = set()
for r in refs:
    m = re.match(r'^([A-Z][\w’\'\-\.]+)', r)
    y = re.search(r'\((\d{4}[a-z]?)\)', r)
    if m and y: keys.add((m.group(1).rstrip('.'), y.group(1)))
# citations in the body: key on the FIRST surname of each citation only
bodytxt = '\n'.join(paras[:ri])
ACK = bodytxt.find('ACKNOWLEDGEMENT')
cites = set()
# parenthetical: (Surname et al., 2019; Surname & Surname, 2020)
for m in re.finditer(r'\(([^()]{3,160})\)', bodytxt):
    if m.start() < 0: continue
    for part in m.group(1).split(';'):
        part = part.strip()
        mm = re.match(r'^([A-Z][\w’\'\-\.]+)[^,]{0,60}?,\s*(\d{4}[a-z]?)$', part)
        if mm: cites.add((mm.group(1).rstrip('.'), mm.group(2)))
# narrative: Surname et al. (2019) / Surname and Surname (2019)
for m in re.finditer(r'\b([A-Z][\w’\'\-\.]+)(?:\s+(?:et al\.|and\s+[A-Z][\w’\'\-]+|&\s*[A-Z][\w’\'\-]+))?\s*\((\d{4}[a-z]?)\)', bodytxt):
    cites.add((re.sub(r'’s$', '', m.group(1).rstrip('.')), m.group(2)))
cites.discard(('Author', '2026'))          # the study-site map is the author's own
unmatched = sorted(c for c in cites if c not in keys)
print(f'   distinct in-text citations: {len(cites)}')
print(f'   citations with no reference entry: {len(unmatched)}'
      + (('  ' + str(unmatched[:12])) if unmatched else ''))
def _sk(t):
    a = re.sub(r'[^a-z ]', '', t.split('(')[0].lower()).strip()
    y = re.search(r'\((\d{4}[a-z]?)\)', t)
    return (a, y.group(1) if y else '')
alpha = [_sk(r) for r in refs]
print(f'   list is alphabetical: {alpha == sorted(alpha)}')

print()
print('2. TABLES AND FIGURES')
tnums = [int(m.group(1)) for p in paras if (m := re.fullmatch(r'Table (\d+)', p))]
fnums = [int(m.group(1)) for p in paras if (m := re.fullmatch(r'Figure (\d+)', p))]
print(f'   table captions {len(tnums)} sequential 1-{max(tnums)}: {tnums == list(range(1, len(tnums)+1))}')
print(f'   figure captions {len(fnums)} sequential 1-{max(fnums)}: {fnums == list(range(1, len(fnums)+1))}')
lt = [i for i, p in enumerate(paras) if p == 'LIST OF TABLES'][-1]
lf = [i for i, p in enumerate(paras) if p == 'LIST OF FIGURES'][-1]
ltab = [p for p in paras[lt+1:lf] if p.startswith('Table ')]
la = [i for i, p in enumerate(paras) if p == 'LIST OF ABBREVIATIONS'][-1]
lfig = [p for p in paras[lf+1:la] if p.startswith('Figure ')]
print(f'   LIST OF TABLES entries: {len(ltab)}   LIST OF FIGURES entries: {len(lfig)}')
# titles must match
capT = {}
for i, e in enumerate(kids):
    if e.tag != qn('w:p'): continue
    m = re.fullmatch(r'(Table|Figure) (\d+)', ptx(e))
    if m: capT[(m.group(1), int(m.group(2)))] = ptx(kids[i+1])
badt = [x for x in ltab if x.split('\t')[0].strip() !=
        f"Table {x.split(':')[0].split()[1]}: {capT[('Table', int(x.split(':')[0].split()[1]))]}"]
badf = [x for x in lfig if x.split('\t')[0].strip() !=
        f"Figure {x.split(':')[0].split()[1]}: {capT[('Figure', int(x.split(':')[0].split()[1]))]}"]
print(f'   list titles that differ from the caption: {len(badt)} tables, {len(badf)} figures')

print()
print('3. FORMATTING')
fonts = collections.Counter(r.get(qn('w:ascii')) for r in body.iter(qn('w:rFonts')))
cols = collections.Counter((c.get(qn('w:val')) or '').upper() for c in body.iter(qn('w:color')))
print(f'   fonts used: {dict(fonts)}')
print(f'   run colours: {dict(cols)}')
shd = [s.get(qn('w:fill')) for s in body.iter(qn('w:shd'))
       if (s.get(qn('w:fill')) or 'auto').upper() not in ('AUTO', 'FFFFFF', '')]
print(f'   shaded cells / runs: {len(shd)}')
notes = [p for p in paras if p.startswith('Note.')]
print(f'   "Note." lines under tables: {len([p for p in notes])} (figures may carry them)')
print(f'   headings without a number: '
      f'{len([p for p in paras if p.startswith("CHAPTER") and ":" not in p])}')

print()
print('4. CHAPTER LENGTHS (words)')
_c1 = [i for i, p in enumerate(paras) if p == 'CHAPTER ONE: INTRODUCTION'][-1]
marks = [(i, p) for i, p in enumerate(paras)
         if i >= _c1 and re.match(r'^CHAPTER (ONE|TWO|THREE|FOUR|FIVE|SIX):', p)]
marks.append((ri, 'REFERENCES'))
for (a, na), (b, _) in zip(marks, marks[1:]):
    wc = sum(len(p.split()) for p in paras[a:b])
    print(f'   {na[:46]:48s} {wc:6,d}')
