# -*- coding: utf-8 -*-
"""Replace Chapters Four to Six inside the full thesis with the freshly built
chapters document: splices body XML, re-relates images, remaps list numbering
and copies over any style the thesis does not already define."""
import copy, re, docx
from docx.oxml.ns import qn

SRC = 'v5/Chapters_Four_to_Six.docx'
DST = 'v3/thesis.docx'
OUT = 'v5/thesis.docx'

new = docx.Document(SRC)
th  = docx.Document(DST)

# ---------------------------------------------------------------- 1. locate
def text(el):
    return ''.join(n.text or '' for n in el.iter(qn('w:t'))).strip()

kids = list(th.element.body)
start = end = None
for i, el in enumerate(kids):
    if el.tag == qn('w:p'):
        t = text(el)
        if start is None and t == 'CHAPTER FOUR: RESULTS':
            start = i
        elif start is not None and t == 'REFERENCES':
            end = i
            break
assert start is not None and end is not None, (start, end)
print(f'replacing thesis body children [{start}, {end}) — {end-start} elements')

# ------------------------------------------------- 2. import the new content
body_new = new.element.body
new_kids = [el for el in body_new if el.tag != qn('w:sectPr')]
frag = [copy.deepcopy(el) for el in new_kids]

# --- 2a. images: relate each source image into the thesis package -----------
rid_map = {}
for el in frag:
    for blip in el.iter(qn('a:blip')):
        rid = blip.get(qn('r:embed'))
        if rid is None:
            continue
        if rid not in rid_map:
            blob = new.part.rels[rid].target_part.blob
            import io
            new_rid, _ = th.part.get_or_add_image(io.BytesIO(blob))
            rid_map[rid] = new_rid
        blip.set(qn('r:embed'), rid_map[rid])
print(f'images re-related: {len(rid_map)}')

# --- 2b. numbering: copy abstractNum/num definitions with fresh ids ---------
try:
    num_new = new.part.numbering_part.element
except Exception:
    num_new = None
num_map = {}
if num_new is not None:
    num_th = th.part.numbering_part.element
    used_abs = {int(a.get(qn('w:abstractNumId')))
                for a in num_th.findall(qn('w:abstractNum'))}
    used_num = {int(n.get(qn('w:numId'))) for n in num_th.findall(qn('w:num'))}
    next_abs = max(used_abs, default=0) + 1
    next_num = max(used_num, default=0) + 1
    abs_by_id = {a.get(qn('w:abstractNumId')): a
                 for a in num_new.findall(qn('w:abstractNum'))}
    for n in num_new.findall(qn('w:num')):
        old_num = n.get(qn('w:numId'))
        ref = n.find(qn('w:abstractNumId'))
        old_abs = ref.get(qn('w:val')) if ref is not None else None
        src_abs = abs_by_id.get(old_abs)
        if src_abs is None:
            continue
        a = copy.deepcopy(src_abs)
        a.set(qn('w:abstractNumId'), str(next_abs))
        nsid = a.find(qn('w:nsid'))
        if nsid is not None:
            a.remove(nsid)
        # abstractNum elements must precede num elements
        first_num = num_th.find(qn('w:num'))
        if first_num is not None:
            first_num.addprevious(a)
        else:
            num_th.append(a)
        nn = copy.deepcopy(n)
        nn.set(qn('w:numId'), str(next_num))
        nn.find(qn('w:abstractNumId')).set(qn('w:val'), str(next_abs))
        # schema order: numPicBullet*, abstractNum*, num*, numIdMacAtCleanup?
        cleanup = num_th.find(qn('w:numIdMacAtCleanup'))
        if cleanup is not None:
            cleanup.addprevious(nn)
        else:
            num_th.append(nn)
        num_map[old_num] = str(next_num)
        next_abs += 1
        next_num += 1
    for el in frag:
        for ni in el.iter(qn('w:numId')):
            v = ni.get(qn('w:val'))
            if v in num_map:
                ni.set(qn('w:val'), num_map[v])
print(f'numbering definitions imported: {len(num_map)} -> {num_map}')

# --- 2c. styles: add any style the thesis lacks -----------------------------
st_th = th.styles.element
have = {s.get(qn('w:styleId')) for s in st_th.findall(qn('w:style'))}
added = []
for s in new.styles.element.findall(qn('w:style')):
    sid = s.get(qn('w:styleId'))
    if sid not in have:
        st_th.append(copy.deepcopy(s))
        have.add(sid)
        added.append(sid)
print(f'styles added: {added}')

# ------------------------------------------------------------- 3. splice in
body = th.element.body
anchor = kids[end]                    # the REFERENCES paragraph
for el in kids[start:end]:
    body.remove(el)
for el in frag:
    anchor.addprevious(el)

th.save(OUT)
print('saved', OUT)
