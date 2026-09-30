# -*- coding: utf-8 -*-
"""Add section 3.10.4 defining the market-structure measures, and put the
concentration and margin figures into the abstract.

Chapter Three and the abstract come from the base document rather than from a
JSON block list, so both are edited on the assembled file, after the merge.
"""
import docx, json, copy
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

MS = json.load(open('v6/market_structure.json'))
o = MS['overall']
site = {r['site']: r for r in MS['by_site']}
m0, m1, m2 = MS['margins']
bp = MS['buyers_per_seller']

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)


def settext(p, t):
    el = p._p
    kids = el.findall(qn('w:r')) + el.findall(qn('w:hyperlink'))
    if not kids:
        return False
    src = kids[0]
    tmpl = copy.deepcopy(src if src.tag == qn('w:r') else src.find(qn('w:r')))
    for c in kids:
        el.remove(c)
    for old in tmpl.findall(qn('w:t')):
        tmpl.remove(old)
    rPr = tmpl.find(qn('w:rPr'))
    if rPr is not None:
        for tag in ('w:color', 'w:u', 'w:rStyle'):
            for e in rPr.findall(qn(tag)):
                rPr.remove(e)
        c = OxmlElement('w:color'); c.set(qn('w:val'), '000000'); rPr.append(c)
    tn = OxmlElement('w:t'); tn.set(qn('xml:space'), 'preserve'); tn.text = t
    tmpl.append(tn)
    el.append(tmpl)
    return True


def clone_after(p, text, style=None):
    new = copy.deepcopy(p._p)
    p._p.addnext(new)
    np_ = docx.text.paragraph.Paragraph(new, p._parent)
    if style:
        np_.style = d.styles[style]
    settext(np_, text)
    return np_


def is_heading(p):
    return (p.style.name or '').startswith('Heading')


# ------------------------------------------------- 1. remove a previous run
ps = d.paragraphs
for p in list(ps):
    if is_heading(p) and p.text.strip().startswith('3.10.4 Market structure, margin'):
        nxt = ps[ps.index(p) + 1]
        nxt._p.getparent().remove(nxt._p)
        p._p.getparent().remove(p._p)
        print('previous 3.10.4 removed')
        break

# --------------------------------------------------- 2. insert section 3.10.4
# anchor on the heading, never on the row for it in the table of contents: an
# earlier version matched the first paragraph starting "3.11 ", which was the
# contents row, and put the whole section inside the table of contents
ps = d.paragraphs
i311 = next(i for i, p in enumerate(ps)
            if is_heading(p) and p.text.strip().startswith('3.11 '))
last = ps[i311 - 1]
assert not is_heading(last), 'nothing to hang 3.10.4 on before 3.11'

head = clone_after(last, '3.10.4 Market structure, margin and dispersion measures',
                   style='Heading 3')
BODY = (
  'Four measures summarise market structure. Concentration at first sale is taken '
  'over the buying points fishers named, using the concentration ratio, the share '
  'of harvesters attached to the largest point, and the Herfindahl-Hirschman '
  'Index, the sum of the squared shares on a scale to 10,000. Dividing 10,000 by '
  'that index gives the numbers-equivalent, the count of equal-sized outlets that '
  'would produce the same concentration. Because the survey recorded where fishers '
  'sold rather than what each buyer handled, these are shares of harvesters and '
  'not shares of volume, and they are reported on that basis. The gross marketing '
  'margin at a node is the difference between that actor’s selling price and '
  'his buying price, expressed as a percentage of his selling price; the total '
  'marketing margin applies the same formula across the whole chain; and the '
  'producer’s share is the fisher mean divided by the final-node mean. '
  'Physical mortality, the one cost the survey measured, is carried through as a '
  'deduction from the volume the harvester realises, which yields a '
  'producer’s share net of that loss. Price dispersion is the coefficient of '
  'variation, the standard deviation divided by the mean, which lets nodes whose '
  'price levels differ by a factor of three be compared directly. All four were '
  'computed in a spreadsheet from the IBM SPSS Statistics output rather than by a '
  'built-in procedure, and the formulas are given in the syntax file.')
clone_after(head, BODY, style='Normal')
print('section 3.10.4 inserted')

# The abstract is written in one place, by v6/fix_abstract.py from
# v6/abstract_text.py, so nothing is appended to it here.

d.save(DOC)
print('saved', DOC)
