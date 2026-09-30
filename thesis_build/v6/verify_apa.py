# -*- coding: utf-8 -*-
"""APA 7 and house-style checks on the finished thesis.

Checks what Word will actually paint: run fonts and colours, cell shading,
table and figure caption shape, the numbering of both, and whether the table of
contents, the list of tables and the list of figures agree with the headings and
captions in the body.
"""
import docx, re, sys
from docx.oxml.ns import qn

D = docx.Document(sys.argv[1] if len(sys.argv) > 1 else 'v6/thesis.docx')
body = list(D.element.body)
def txt(el): return ''.join(t.text or '' for t in el.iter(qn('w:t')))
fails = []
def check(ok, label, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + label)
    if detail: print('        ' + detail)
    if not ok: fails.append(label)

# ---------------------------------------------------------------- 1. shading
shaded = []
for i, el in enumerate(body):
    if el.tag != qn('w:tbl'):
        continue
    for sh in el.iter(qn('w:shd')):
        fill = (sh.get(qn('w:fill')) or '').upper()
        val = (sh.get(qn('w:val')) or '').lower()
        if fill not in ('', 'AUTO', 'FFFFFF') or val not in ('', 'clear', 'nil'):
            shaded.append(f'{fill or val}')
check(not shaded, 'No table cell carries a fill or pattern',
      f'shaded cells: {len(shaded)}' if shaded else 'every cell is white')

# ---------------------------------------------------------------- 2. colour
coloured = set()
for c in D.element.body.iter(qn('w:color')):
    v = (c.get(qn('w:val')) or '').upper()
    if v not in ('000000', 'AUTO', ''):
        coloured.add(v)
check(not coloured, 'No run is set in a colour other than black',
      f'colours found: {sorted(coloured)}' if coloured else 'black or automatic throughout')

# ------------------------------------------------- 2b. bold in the body text
# the house style bolds the chapter and front-matter headings, the "Table N"
# and "Figure N" lines and the table header rows. A bold sentence is a mistake:
# the critical assessment in section 2.10 was once cloned from the bold
# submission statement on the title page and came out bold throughout.
def is_on(rp, tag):
    if rp is None: return False
    e = rp.find(qn(tag))
    return e is not None and (e.get(qn('w:val')) or 'true') not in ('0', 'false', 'off')

ch1 = next(i for i, el in enumerate(body)
           if el.tag == qn('w:p') and txt(el).strip().upper().startswith('CHAPTER ONE'))
refs = max(i for i, el in enumerate(body)
           if el.tag == qn('w:p') and txt(el).strip().upper() == 'REFERENCES')
boldsent = []
for el in body[ch1:refs]:
    if el.tag != qn('w:p'):
        continue
    t = txt(el).strip()
    pr = el.find(qn('w:pPr'))
    st = pr.find(qn('w:pStyle')) if pr is not None else None
    styled = (st.get(qn('w:val')) or '') if st is not None else ''
    if (styled.startswith('Heading') or len(t.split()) <= 12
            or re.fullmatch(r'(Table|Figure) \d+', t)):
        continue
    for r in el.findall(qn('w:r')):
        rt = ''.join(x.text or '' for x in r.findall(qn('w:t')))
        if rt.strip() and is_on(r.find(qn('w:rPr')), 'w:b'):
            boldsent.append(t[:60]); break
check(not boldsent, 'No sentence in Chapters One to Six is set in bold',
      f'{len(boldsent)} bold paragraphs: {boldsent[:3]}' if boldsent else
      'bold is confined to headings, exhibit numbers and table headers')

# ---------------------------------------------------------------- 3. font
bad_font = {}
for rf in D.element.body.iter(qn('w:rFonts')):
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        v = rf.get(qn(a))
        if v and v != 'Times New Roman':
            bad_font[v] = bad_font.get(v, 0) + 1
check(not bad_font, 'Every explicit run font is Times New Roman',
      f'other fonts: {bad_font}' if bad_font else 'no other typeface is named')

# body text must be 12 pt; APA 7 allows 8 to 12 pt inside a table, and a title
# page may be larger, so those are counted separately
psz, tsz = {}, {}
for el in body:
    d = tsz if el.tag == qn('w:tbl') else psz
    for sz in el.iter(qn('w:sz')):
        v = sz.get(qn('w:val'))
        if v: d[v] = d.get(v, 0) + 1
big = {k: v for k, v in psz.items() if int(k) > 24}
check(set(psz) <= {'24'} | set(big), 'Body paragraphs are set in 12 pt',
      'larger only on the title page: ' + ', '.join(f'{int(k)/2:g} pt x{v}' for k, v in sorted(big.items()))
      if big else 'all 12 pt')
check(all(16 <= int(k) <= 24 for k in tsz), 'Table text is within the 8 to 12 pt APA range',
      ', '.join(f'{int(k)/2:g} pt x{v}' for k, v in sorted(tsz.items())))

# --------------------------------------------- 4. captions: shape and sequence
tab_caps, fig_caps = [], []
for i, el in enumerate(body):
    if el.tag != qn('w:p'):
        continue
    t = txt(el).strip()
    m = re.fullmatch(r'Table (\d+)', t)
    if m: tab_caps.append((i, int(m.group(1))))
    m = re.fullmatch(r'Figure (\d+)', t)
    if m: fig_caps.append((i, int(m.group(1))))

tn = [n for _, n in tab_caps]
fn = [n for _, n in fig_caps]
check(tn == sorted(set(tn)) and tn == list(range(1, len(tn) + 1)),
      f'Tables are numbered 1 to {len(tn)} in one sequence',
      f'first {tn[:6]} … last {tn[-3:]}')
check(fn == sorted(set(fn)) and fn == list(range(1, len(fn) + 1)),
      f'Figures are numbered 1 to {len(fn)} in one sequence',
      f'first {fn[:6]} … last {fn[-3:]}')

# APA 7: the number on its own line, the title in italics on the next line
def title_after(i):
    j = i + 1
    while j < len(body) and body[j].tag == qn('w:p') and not txt(body[j]).strip():
        j += 1
    return j

bad_shape = []
for i, n in tab_caps + fig_caps:
    j = title_after(i)
    if j >= len(body) or body[j].tag != qn('w:p'):
        bad_shape.append((n, 'no title paragraph')); continue
    t = txt(body[j]).strip()
    if not t:
        bad_shape.append((n, 'empty title')); continue
    its = [r.find(qn('w:rPr')) is not None and
           r.find(qn('w:rPr')).find(qn('w:i')) is not None
           for r in body[j].findall(qn('w:r')) if (txt(r) or '').strip()]
    if not its or not all(its):
        bad_shape.append((n, f'title not fully italic: {t[:40]}'))
check(not bad_shape, 'Every caption is the number on one line and an italic title on the next',
      f'{len(bad_shape)} exceptions: {bad_shape[:4]}' if bad_shape else
      f'{len(tab_caps)} table and {len(fig_caps)} figure captions')

# ------------------------------------- 5. lists of tables and figures vs body
def titles(caps):
    out = {}
    for i, n in caps:
        out[n] = re.sub(r'\s+', ' ', txt(body[title_after(i)])).strip()
    return out
bodyT, bodyF = titles(tab_caps), titles(fig_caps)

def marks(head):
    return [k for k, el in enumerate(body)
            if el.tag == qn('w:p') and txt(el).strip().upper() == head]

def listed(head):
    # the first occurrence is the row for it inside the table of contents; the
    # list itself is the last one
    i = marks(head)[-1]
    out = {}
    for el in body[i + 1:]:
        if el.tag != qn('w:p'):
            continue
        t = re.sub(r'\s+', ' ', txt(el)).strip()
        if not t: continue
        m = re.match(r'^(Table|Figure)\s*(\d+)\s*[:.]?\s+(.*?)\s*(\d+)?$', t)
        if not m: break
        out[int(m.group(2))] = m.group(3).strip()
    return out
lotT, lofF = listed('LIST OF TABLES'), listed('LIST OF FIGURES')

for name, bodyd, listd in (('tables', bodyT, lotT), ('figures', bodyF, lofF)):
    miss = sorted(set(bodyd) - set(listd))
    extra = sorted(set(listd) - set(bodyd))
    wrong = [n for n in sorted(set(bodyd) & set(listd))
             if bodyd[n].rstrip('.').lower() != listd[n].rstrip('.').lower()]
    check(not (miss or extra or wrong),
          f'The list of {name} matches the captions in the body',
          f'{len(listd)} entries for {len(bodyd)} {name}' if not (miss or extra or wrong)
          else f'missing {miss} extra {extra} different titles {wrong[:5]}')

# ---------------------------------------------------------- 6. contents vs headings
heads = [re.sub(r'\s+', ' ', txt(el)).strip() for el in body
         if el.tag == qn('w:p') and (el.find(qn('w:pPr')) is not None)
         and el.find(qn('w:pPr')).find(qn('w:pStyle')) is not None
         and (el.find(qn('w:pPr')).find(qn('w:pStyle')).get(qn('w:val')) or '')
             .startswith('Heading')]
i = marks('TABLE OF CONTENTS')[0]
stop = marks('LIST OF TABLES')[-1]        # where the real list of tables begins
toc = []
for el in body[i + 1:stop]:
    if el.tag != qn('w:p'):
        continue
    t = re.sub(r'\s+', ' ', txt(el)).strip()
    if t: toc.append(re.sub(r'\s*\d+$', '', t).strip())
front = {'LIST OF TABLES', 'LIST OF FIGURES', 'LIST OF ABBREVIATIONS', 'REFERENCES',
         'APPENDICES'}
missing = [h for h in heads if h not in toc and h.upper() not in front]
strays = [t for t in toc if t not in heads and t.upper() not in front]
check(not (missing or strays), 'Every heading appears in the table of contents and vice versa',
      f'{len(toc)} contents rows for {len(heads)} headings' if not (missing or strays)
      else f'headings missing from contents: {missing[:4]}; contents rows with no heading: {strays[:4]}')

# ----------------------------------------------------- 7. heading case and numbering
badcase = [h for h in heads
           if re.match(r'^\d+(\.\d+)*\s', h) and re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+', h)]
print(f'INFO  numbered headings in title case: {len(badcase)} (APA 7 allows title case for headings)')

dup = [h for h in set(heads) if heads.count(h) > 1]
check(not dup, 'No heading text is repeated', f'repeated: {dup[:4]}' if dup else '')

nums = [h.split(' ', 1)[0] for h in heads if re.match(r'^\d+\.\d', h)]
gaps = []
for a, b in zip(nums, nums[1:]):
    pa, pb = [int(x) for x in a.split('.')], [int(x) for x in b.split('.')]
    if len(pb) == len(pa) and pb[:-1] == pa[:-1] and pb[-1] != pa[-1] + 1:
        gaps.append(f'{a} -> {b}')
check(not gaps, 'Section numbers run without a gap or repeat',
      f'breaks: {gaps}' if gaps else f'{len(nums)} numbered sections')

print()
print('APA / house-style failures:', len(fails))
for f in fails: print('   -', f)
sys.exit(0)
