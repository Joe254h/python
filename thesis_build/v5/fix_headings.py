# -*- coding: utf-8 -*-
"""Number every chapter and section the same way across all six chapters.

The revised draft carried three different regimes: Chapters One and Two used
Word list numbering with unnumbered subsections, Chapter Three had no chapter
number at all, and Chapters Four to Six were typed by hand. All of them are
now typed by hand in one style, and the stale list numbering is removed."""
import docx, re
from docx.oxml.ns import qn

DOC = 'v5/thesis.docx'
d = docx.Document(DOC)
WORD = {1: 'ONE', 2: 'TWO', 3: 'THREE', 4: 'FOUR', 5: 'FIVE', 6: 'SIX'}
CHAPTER_TITLE = {1: 'INTRODUCTION', 2: 'LITERATURE REVIEW', 3: 'MATERIALS AND METHODS',
                 4: 'RESULTS', 5: 'DISCUSSION', 6: 'CONCLUSIONS AND RECOMMENDATIONS'}
FRONT = {'DECLARATION', 'DEDICATION', 'ACKNOWLEDGEMENT', 'ABSTRACT', 'TABLE OF CONTENTS',
         'LIST OF TABLES', 'LIST OF FIGURES', 'REFERENCES', 'APPENDICES',
         'LIST OF ABBREVIATIONS', 'LIST OF ACRONYMS'}

def strip_num(p):
    pPr = p._p.find(qn('w:pPr'))
    if pPr is None: return
    for n in pPr.findall(qn('w:numPr')):
        pPr.remove(n)

def set_text(p, text):
    runs = p._p.findall(qn('w:r'))
    if not runs:
        return
    done = False
    for t in runs[0].iter(qn('w:t')):
        t.text = text; t.set(qn('xml:space'), 'preserve'); done = True; break
    if not done:
        return
    for r in runs[1:]:
        p._p.remove(r)

ch = 0; sec = 0; sub = 0
changed = []
for p in d.paragraphs:
    t = p.text.strip()
    st = p.style.name if p.style is not None else ''
    if not t or not st.startswith('Heading'):
        continue
    bare = re.sub(r'^(CHAPTER\s+[A-Z0-9]+\s*[:.]?\s*|\d+(\.\d+)*\s+)', '', t).strip()
    if st == 'Heading 1':
        if bare.upper() in FRONT or t.upper() in FRONT:
            strip_num(p); continue
        ch += 1; sec = 0; sub = 0
        new = f'CHAPTER {WORD[ch]}: {CHAPTER_TITLE.get(ch, bare.upper())}'
    elif st == 'Heading 2':
        if ch == 0: continue
        sec += 1; sub = 0
        new = f'{ch}.{sec} {bare}'
    elif st == 'Heading 3':
        if ch == 0 or sec == 0: continue
        sub += 1
        new = f'{ch}.{sec}.{sub} {bare}'
    else:
        continue
    strip_num(p)
    if new != t:
        set_text(p, new); changed.append((t[:46], new[:56]))

d.save(DOC)
print(f'headings renumbered: {len(changed)}')
for a, b in changed[:14]:
    print(f'   {a!r}\n    -> {b!r}')
print('   ...')
for a, b in changed[-6:]:
    print(f'   {a!r}\n    -> {b!r}')
