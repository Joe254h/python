# -*- coding: utf-8 -*-
"""Carry the trimmed text into the candidate's own file.

The candidate's copy differs from the build only in formatting: they reapplied
the heading styles, which dropped direct bold and the centring on the Chapter
Four to Six headings, and they removed the bold that the build had left on the
body paragraphs of section 2.10. Rebuilding would undo all of that, so the text
is carried the other way instead: their file stays the master for formatting,
and each paragraph whose wording changed is rewritten inside it, keeping its own
run properties.

Bookmarks in a paragraph being removed are moved to the paragraph before it, so
no cross-reference in the table of contents is left dangling.
"""
import copy, difflib, re, shutil, sys
import docx
from docx.oxml.ns import qn

SRC = 'v8/kkk.docx'                     # the candidate's file
REF = 'v6/thesis.docx'                  # the verified build, with the trimmed text
OUT = 'v8/thesis_trimmed.docx'
shutil.copy(SRC, OUT)

ref = docx.Document(REF)
out = docx.Document(OUT)


def txt(el):
    return re.sub(r'\s+', ' ', ''.join(t.text or '' for t in el.iter(qn('w:t')))).strip()


def paras(d):
    """Body paragraphs that carry text, in order, with their element."""
    return [(el, txt(el)) for el in list(d.element.body)
            if el.tag == qn('w:p') and txt(el)]


def retext(el, t):
    """Replace the text, keeping the first run's character formatting."""
    runs = el.findall(qn('w:r'))
    if not runs:
        return False
    keep = runs[0]
    for r in runs[1:]:
        el.remove(r)
    for old in keep.findall(qn('w:t')):
        keep.remove(old)
    tn = keep.makeelement(qn('w:t'), {})
    tn.set(qn('xml:space'), 'preserve')
    tn.text = t
    keep.append(tn)
    return True


def drop(el, prev):
    """Remove the paragraph, rehoming any bookmark it carries."""
    moved = 0
    for tag in ('w:bookmarkStart', 'w:bookmarkEnd'):
        for bm in el.findall(qn(tag)):
            el.remove(bm)
            if prev is not None:
                # w:pPr has to stay the first child, so the bookmark goes after it
                at = 1 if prev.find(qn('w:pPr')) is not None else 0
                prev.insert(at, bm)
                moved += 1
    el.getparent().remove(el)
    return moved


A = paras(out)          # theirs
B = paras(ref)          # the build
sm = difflib.SequenceMatcher(None, [t for _, t in A], [t for _, t in B], autojunk=False)

changed = removed = added = homed = 0
report = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        continue
    old, new = A[i1:i2], B[j1:j2]
    n = min(len(old), len(new))
    for k in range(n):
        if old[k][1] != new[k][1]:
            retext(old[k][0], new[k][1])
            changed += 1
            report.append(('edit', old[k][1][:60], new[k][1][:60]))
    for k in range(n, len(old)):                       # in theirs, not in the build
        prev = A[i1 + k - 1][0] if i1 + k > 0 else None
        homed += drop(old[k][0], prev)
        removed += 1
        report.append(('remove', old[k][1][:60], ''))
    for k in range(n, len(new)):                       # in the build, not in theirs
        anchor = A[i2 - 1][0] if i2 > i1 else (A[i1 - 1][0] if i1 else None)
        if anchor is None:
            print('cannot place an inserted paragraph; aborting')
            sys.exit(1)
        clone = copy.deepcopy(anchor)
        anchor.addnext(clone)
        for tg in ('w:bookmarkStart', 'w:bookmarkEnd'):
            for bm in clone.findall(qn(tg)):
                clone.remove(bm)
        retext(clone, new[k][1])
        added += 1
        report.append(('add', '', new[k][1][:60]))

# Removing paragraphs shifts the alignment, so a paragraph can end up holding
# another one's text while keeping its own style: a heading carrying body text.
# The texts now match the build one for one, so the paragraph style is taken
# from it. Only the style; the candidate's own run formatting stays.
def style_el(el):
    pr = el.find(qn('w:pPr'))
    return None if pr is None else pr.find(qn('w:pStyle'))

def style_of(el):
    st = style_el(el)
    return None if st is None else st.get(qn('w:val'))

A2, B2 = paras(out), paras(ref)
restyled = 0
if [t for _, t in A2] == [t for _, t in B2]:
    for (ael, _), (bel, _) in zip(A2, B2):
        want = style_of(bel)
        if style_of(ael) == want:
            continue
        pr = ael.find(qn('w:pPr'))
        if pr is None:
            pr = ael.makeelement(qn('w:pPr'), {})
            ael.insert(0, pr)
        st = style_el(ael)
        if want is None:
            if st is not None:
                pr.remove(st)
        else:
            if st is None:
                st = pr.makeelement(qn('w:pStyle'), {})
                pr.insert(0, st)
            st.set(qn('w:val'), want)
        restyled += 1
else:
    print('WARNING: paragraph texts do not line up one for one; styles left alone')

# the one bold full stop the candidate's pass left behind
strays = 0
for p in out.paragraphs:
    if not p.text.strip():
        continue
    for r in p._p.findall(qn('w:r')):
        rp = r.find(qn('w:rPr'))
        if rp is None:
            continue
        b = rp.find(qn('w:b'))
        if b is None:
            continue
        body = ''.join(x.text or '' for x in r.findall(qn('w:t')))
        # a bold run inside a sentence is a leftover, not a heading
        if len(p.text.split()) > 12 and len(body.strip()) <= 2:
            rp.remove(b)
            for bcs in rp.findall(qn('w:bCs')):
                rp.remove(bcs)
            strays += 1

out.save(OUT)
print(f'paragraphs rewritten : {changed}')
print(f'paragraphs removed   : {removed}   bookmarks rehomed: {homed}')
print(f'paragraphs added     : {added}')
print(f'paragraphs restyled  : {restyled}')
print(f'stray bold runs fixed: {strays}')
print()
for kind, a, b in report[:6]:
    print(f'  {kind:6s} {a}')
    if b: print(f'         -> {b}')
print(f'  ... {len(report)} changes in all')
