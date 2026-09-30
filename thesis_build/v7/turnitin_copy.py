# -*- coding: utf-8 -*-
"""Write a copy of the thesis without the questionnaire appendix.

Turnitin will only run its AI writing check on a submission of fewer than
30,000 words of qualifying text. The thesis itself is now under that ceiling,
but the margin is about a thousand words, and Turnitin counts a little
differently from any script. This copy drops Appendix A, the questionnaire,
which is the instrument rather than the candidate's own writing, and brings the
count down by a further two thousand words. It is for the Turnitin submission
only; the thesis that goes to the university is the complete file.
"""
import docx, re, shutil
from docx.oxml.ns import qn

import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'v6/thesis_turnitin.docx'
shutil.copy(SRC, OUT)

d = docx.Document(OUT)
body = d.element.body
def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))
def wc(t): return len([w for w in re.split(r'\s+', t.strip()) if w])

els = list(body)
marks = [i for i, el in enumerate(els)
         if el.tag == qn('w:p') and txt(el).strip().upper() == 'APPENDICES']
assert marks, 'no APPENDICES heading found'
start = marks[-1] + 1          # keep the heading, drop what follows it

removed = 0
for el in els[start:]:
    if el.tag in (qn('w:p'), qn('w:tbl')):
        removed += wc(txt(el))
    body.remove(el)

note = d.add_paragraph(
    'The questionnaire is reproduced in the thesis submitted to the university. It is '
    'omitted from this copy, which exists only to bring the submission within the word '
    'limit of the Turnitin AI writing check.')
note.style = d.styles['Normal']

d.save(OUT)
kept = sum(wc(txt(el)) for el in list(body) if el.tag == qn('w:p'))
print(f'{OUT}: appendix removed ({removed:,} words)   paragraph words now {kept:,}')
