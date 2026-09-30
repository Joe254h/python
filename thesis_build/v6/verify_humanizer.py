# -*- coding: utf-8 -*-
"""Scan the finished thesis for the AI writing patterns in Wikipedia's
"Signs of AI writing", which the humanizer guidance is built on.

Numeric en dashes (a range such as 18–35) and the Kruskal–Wallis name keep
their dashes, because one is a range and the other is a compound surname.
"""
import docx, re, collections
from docx.oxml.ns import qn

import sys
D = docx.Document(sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx')
def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))
els = [el for el in list(D.element.body) if el.tag == qn('w:p')]
# the candidate's own prose: the abstract through the end of Chapter Six. The
# reference list and the questionnaire reproduce other people's wording and are
# not rewritten to a style rule.
lo = next(i for i, el in enumerate(els) if txt(el).strip().upper() == 'ABSTRACT')
hi = max(i for i, el in enumerate(els) if txt(el).strip().upper() == 'REFERENCES')
paras = [txt(el) for el in els[lo:hi]]
prose = '\n'.join(paras)
# compound names that legitimately take an en dash
COMPOUNDS = ('Kruskal–Wallis', 'Herfindahl–Hirschman', 'Structure–Conduct–Performance')
scan = prose
for c in COMPOUNDS:
    scan = scan.replace(c, c.replace('–', '-'))

PATTERNS = {
 'em dash used as a break': r'—',
 'en dash outside a number range or a compound name':
     r'(?<![\d\s])–(?!\d)|(?<=\s)–(?=\s)',
 'curly quotation mark': r'[“”]',
 'emoji or decorative symbol': r'[\U0001F300-\U0001FAFF✅✔⚠]',
 'testament / tapestry / landscape (abstract)': r'\b(testament|tapestry)\b|\blandscape of\b',
 'delve / underscore / showcase / foster': r'\b(delve[sd]?|underscor\w+|showcas\w+|foster\w+)\b',
 'pivotal / crucial / vital / groundbreaking': r'\b(pivotal|crucial|vital|groundbreaking)\b',
 'serves as / stands as / marks a shift': r'\b(serves as|stands as|marks a (shift|turning))\b',
 'not only ... but also': r'\bnot only\b[^.]{0,80}\bbut (also|)\b',
 'not merely X but Y': r'\bnot (merely|just) \w[^.]{0,60}\bbut\b',
 'it is important to note': r'\b(it is important to note|it is worth noting|worth stating plainly)\b',
 'in today\'s ... landscape': r"in today'?s\b",
 'a testament to': r'\ba testament to\b',
 'reflects broader / underscores its importance':
     r'\b(reflects (a )?broader|underscores its (importance|significance))\b',
 'excessive hedging stack': r'\b(could potentially|might arguably|may possibly)\b',
 'chatbot artefact': r'\b(I hope this helps|Let me know|Certainly!|Of course!)\b',
 'knowledge-cutoff disclaimer': r'\b(as of my last|up to my last training)\b',
 'generic upbeat close': r'\b(the future looks bright|exciting times)\b',
 'bold mini-heading list item': r'^\s*[-•]\s*\*\*',
}

total = 0
for label, pat in PATTERNS.items():
    hits = list(re.finditer(pat, scan, re.I | re.M))
    if not hits:
        continue
    total += len(hits)
    print(f'  {len(hits):3d}  {label}')
    for m in hits[:4]:
        s = re.sub(r'\s+', ' ', scan[max(0, m.start() - 60):m.end() + 60])
        print(f'        …{s}…')

# rule of three: three comma-separated noun phrases closed with "and", counted
# rather than listed, since a three-item list is often the right answer
threes = len(re.findall(r'\b\w+, \w+ and \w+\b', prose))
print(f'\nAI writing patterns found: {total}')
print(f'three-item lists (informational, not a fault in itself): {threes}')
