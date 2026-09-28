# -*- coding: utf-8 -*-
"""Keep Table 1, the objective-to-analysis table in section 3.9, in step with
the chapter.

The ranges in its last column and the analyses named in its third were written
by hand and went stale every time a table was added or the set reordered. Both
are now derived from the chapter itself.
"""
import docx, json, re
from docx.oxml.ns import qn

DOC = 'v6/thesis.docx'
ch4 = json.load(open('v6/ch4.json'))

# ---- what each objective actually reports
cur, g = None, {}
for b in ch4:
    if b['k'] == 'h2':
        m = re.match(r'4\.(\d)', b['t'])
        cur = {'3': 1, '4': 2, '5': 3}.get(m.group(1)) if m else None
    if cur and b['k'] in ('table', 'fig'):
        g.setdefault((cur, b['k']), []).append(b['n'])

def rng(o):
    t = sorted(g.get((o, 'table'), []))
    f = sorted(g.get((o, 'fig'), []))
    out = f'Tables {t[0]}–{t[-1]}' if t else ''
    if f:
        out += f', Figures {f[0]}–{f[-1]}'
    return out

ANALYSIS = {
 2: ('Frequencies and valid percentages by actor category; descriptive statistics '
     'for prices; Kruskal–Wallis for price by actor category and by study site '
     'within actor; Herfindahl-Hirschman concentration of first-sale outlets and '
     'buyer options per harvester; gross marketing margin at each node, total '
     'marketing margin and the producer’s share gross and net of measured '
     'physical loss; price dispersion and price transmission; actor-specific Monte '
     'Carlo chi-square against study site'),
}

d = docx.Document(DOC)
target = None
for t in d.tables:
    if 'Variables measured' in ' '.join(c.text for c in t.rows[0].cells):
        target = t
        break
if target is None:
    print('alignment table not found'); raise SystemExit

def settext(cell, text):
    p = cell.paragraphs[0]
    if not p.runs:
        return False
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ''
    for extra in cell.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    return True

n = 0
for i, row in enumerate(target.rows[1:], start=1):
    o = i
    if o not in (1, 2, 3):
        continue
    if o in ANALYSIS and settext(row.cells[2], ANALYSIS[o]):
        n += 1
    if settext(row.cells[3], rng(o)):
        n += 1

d.save(DOC)
print('alignment table cells updated:', n)
for o in (1, 2, 3):
    print(f'   Objective {o}: {rng(o)}')
