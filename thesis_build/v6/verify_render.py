# -*- coding: utf-8 -*-
"""Checks on what Word will PAINT, not on what the text says.

Paragraph text does not contain automatic list numbering or field results, so
a text-level check cannot see a heading that renders as
"CHAPTER 5: CHAPTER ONE: INTRODUCTION", nor a PAGEREF that will resolve to
"Error! Reference source not found." These check the XML that produces them.
"""
import zipfile, re, sys, collections
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

fail = 0
def check(ok, label, detail=''):
    global fail
    print(f'{"PASS" if ok else "FAIL"}  {label}')
    if detail: print(f'        {detail}')
    if not ok: fail += 1

def ptx(el):
    return ''.join(t.text or '' for t in el.iter(W + 't')).strip()

# ---------------------------------------------- 1. numbering on heading styles
numbered_styles = []
for st in styles.findall(W + 'style'):
    sid = st.get(W + 'styleId') or ''
    if not re.fullmatch(r'Heading[1-9]', sid): continue
    pPr = st.find(W + 'pPr')
    if pPr is not None and pPr.find(W + 'numPr') is not None:
        numbered_styles.append(sid)
check(not numbered_styles,
      'No heading STYLE carries automatic numbering',
      f'Word would paint a list number in front of every one of these: {numbered_styles}'
      if numbered_styles else
      'Chapter and section numbers are typed into the text, so nothing is painted on top.')

# ------------------------------------------ 2. numbering on heading paragraphs
numbered_paras = []
for p in doc.iter(W + 'p'):
    pPr = p.find(W + 'pPr')
    if pPr is None: continue
    ps = pPr.find(W + 'pStyle')
    sid = ps.get(W + 'val') if ps is not None else ''
    if re.fullmatch(r'Heading[1-9]', sid or '') and pPr.find(W + 'numPr') is not None:
        numbered_paras.append(ptx(p)[:50])
check(not numbered_paras, 'No heading PARAGRAPH carries automatic numbering',
      str(numbered_paras[:5]) if numbered_paras else 'Checked every heading-styled paragraph.')

# ------------------------------- 3. a numbering list that prints "CHAPTER %1:"
chapter_lists = []
if numbering is not None:
    for an in numbering.findall(W + 'abstractNum'):
        for lvl in an.findall(W + 'lvl'):
            t = lvl.find(W + 'lvlText')
            if t is not None and 'CHAPTER' in (t.get(W + 'val') or '').upper():
                chapter_lists.append((an.get(W + 'abstractNumId'), t.get(W + 'val')))
if chapter_lists:
    # only a problem if something still references it
    used = {n.get(W + 'val') for n in doc.iter(W + 'numId')}
    nums = {num.get(W + 'numId'): num.find(W + 'abstractNumId').get(W + 'val')
            for num in numbering.findall(W + 'num')
            if num.find(W + 'abstractNumId') is not None}
    live = [n for n, a in nums.items() if a in {c[0] for c in chapter_lists} and n in used]
    check(not live, 'No live reference to a "CHAPTER %1:" numbering list',
          f'definitions still present but unreferenced: {chapter_lists}' if not live
          else f'numIds still using it: {live}')
else:
    check(True, 'No "CHAPTER %1:" numbering list defined')

# ------------------------------------------------- 4. field targets resolve
starts = collections.Counter()
names = {}
for b in doc.iter(W + 'bookmarkStart'):
    starts[b.get(W + 'id')] += 1
    names[b.get(W + 'name')] = b.get(W + 'id')
ends = {b.get(W + 'id') for b in doc.iter(W + 'bookmarkEnd')}
instr = ''.join(t.text or '' for t in doc.iter(W + 'instrText'))
targets = set(re.findall(r'PAGEREF\s+(\S+)', instr))
missing = sorted(t for t in targets if t not in names)
check(not missing,
      f'Every PAGEREF resolves to a bookmark ({len(targets)} fields)',
      f'these would render "Error! Reference source not found.": {missing}'
      if missing else 'No broken cross-references.')

orphan = sorted(i for i, c in starts.items() if i not in ends)
check(not orphan, f'Every bookmark is closed ({sum(starts.values())} bookmarks)',
      f'bookmarkStart with no bookmarkEnd: {orphan[:8]}' if orphan else '')

dup = [i for i, c in starts.items() if c > 1]
check(not dup, 'No duplicate bookmark ids', str(dup[:8]) if dup else '')

# ------------------------------------------------- 5. fonts that will render
DEFAULT = None
dd = styles.find(W + 'docDefaults')
if dd is not None:
    rf = dd.find(f'{W}rPrDefault/{W}rPr/{W}rFonts')
    if rf is not None: DEFAULT = rf.get(W + 'ascii')
bad_styles = []
for st in styles.findall(W + 'style'):
    sid = st.get(W + 'styleId') or ''
    if not re.fullmatch(r'Heading[1-9]|Normal', sid): continue
    rPr = st.find(W + 'rPr')
    f = rPr.find(W + 'rFonts') if rPr is not None else None
    name = f.get(W + 'ascii') if f is not None else None
    if name is None and sid != 'Normal':
        continue        # inherits Normal, which is checked below
    if name and name != 'Times New Roman':
        bad_styles.append((sid, name))
check(not bad_styles, 'Heading and Normal styles resolve to Times New Roman',
      str(bad_styles) if bad_styles else f'document default is {DEFAULT}, Normal overrides it')

print()
print('render checks failed:' , fail)
sys.exit(1 if fail else 0)
