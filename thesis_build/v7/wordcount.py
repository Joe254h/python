# -*- coding: utf-8 -*-
"""Count the words Turnitin would see.

Turnitin's AI writing detection reads long-form prose and skips tables, so the
number that matters against its 30,000-word ceiling is the paragraph count, not
the whole document. The file the candidate submitted had 30,471 paragraph words
and Turnitin reported the qualifying text as over 30,000, which is how we know
which count to watch.
"""
import docx, re, sys
from docx.oxml.ns import qn

path = sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx'
d = docx.Document(path)
def wc(t): return len([w for w in re.split(r'\s+', t.strip()) if w])
def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))

para = tbl = 0
for el in list(d.element.body):
    if el.tag == qn('w:p'): para += wc(txt(el))
    elif el.tag == qn('w:tbl'): tbl += wc(txt(el))

# the questionnaire appendix, which is the instrument rather than the
# candidate's own prose
els = list(d.element.body)
q = [i for i, el in enumerate(els)
     if el.tag == qn('w:p') and txt(el).strip().upper() == 'APPENDICES']
appendix = 0
if q:
    for el in els[q[-1]:]:
        if el.tag == qn('w:p'): appendix += wc(txt(el))

print(f'{path}')
print(f'  paragraph words (what Turnitin counts) : {para:,}')
print(f'  table words (not counted)              : {tbl:,}')
print(f'  whole document                         : {para + tbl:,}')
print(f'  of which the questionnaire appendix    : {appendix:,}')
print(f'  paragraphs without that appendix       : {para - appendix:,}')
print(f'  margin under 30,000                    : {30000 - para:,}')
