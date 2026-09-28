# -*- coding: utf-8 -*-
"""Strip automatic numbering from the heading STYLES.

The source document defined Heading 1 to 4 with numPr pointing at an
abstract numbering list whose level 0 reads "CHAPTER %1:" starting at 5 and
whose level 1 reads "%1.%2" starting at 4. Because every chapter and section
number in this thesis is typed into the text, Word painted that list on top
of it and rendered "CHAPTER 5: CHAPTER ONE: INTRODUCTION" and
"5.4 1.1 Background information".

Stripping numPr from a paragraph is not enough: numId 1 never appears on a
paragraph, it is inherited from the style. This removes it at the style, and
also from any heading paragraph that carries one directly.
"""
import zipfile, shutil, re, os
from lxml import etree

DOC = 'v6/thesis.docx'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
TMP = DOC + '.tmp'

zin = zipfile.ZipFile(DOC)
names = [n for n in zin.namelist() if not n.endswith('/')]
data = {n: zin.read(n) for n in names}
zin.close()

# ---------------------------------------------------------- 1. the styles
root = etree.fromstring(data['word/styles.xml'])
stripped = []
for st in root.findall(W + 'style'):
    sid = st.get(W + 'styleId') or ''
    if not re.fullmatch(r'Heading[1-9]', sid):
        continue
    pPr = st.find(W + 'pPr')
    if pPr is None:
        continue
    for n in pPr.findall(W + 'numPr'):
        pPr.remove(n)
        stripped.append(sid)
data['word/styles.xml'] = etree.tostring(root, xml_declaration=True,
                                         encoding='UTF-8', standalone=True)
print('numPr removed from heading styles:', stripped or 'none found')

# ------------------------------------------- 2. any heading paragraph too
doc = etree.fromstring(data['word/document.xml'])
para = 0
for p in doc.iter(W + 'p'):
    pPr = p.find(W + 'pPr')
    if pPr is None:
        continue
    ps = pPr.find(W + 'pStyle')
    sid = ps.get(W + 'val') if ps is not None else ''
    if not re.fullmatch(r'Heading[1-9]', sid or ''):
        continue
    for n in pPr.findall(W + 'numPr'):
        pPr.remove(n); para += 1
data['word/document.xml'] = etree.tostring(doc, xml_declaration=True,
                                           encoding='UTF-8', standalone=True)
print('numPr removed from heading paragraphs:', para)

# ------------------------------------------------------------ 3. repack
first = '[Content_Types].xml'
order = [first] + [n for n in names if n != first]
with zipfile.ZipFile(TMP, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in order:
        z.writestr(n, data[n])
os.replace(TMP, DOC)
print('saved', DOC)
