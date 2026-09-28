# -*- coding: utf-8 -*-
"""One presentation per variable.

Chapter Four showed 27 of its 33 figures alongside a table of the same
variable. This keeps exactly one of each:

  - where the variable's association with BMU is significant, the table stays,
    because it carries all four actors, the site pattern, chi-square, df, p and
    the 99% confidence interval, and the figure goes;
  - otherwise the figure stays and that variable's block is removed from the
    table. The non-significant p-value is already stated in the prose.

A paragraph that opened "Table 12 shows ..." for a table that has gone is
re-pointed at the figure that replaced it, and the figure is moved up to sit
where the table was, so it still precedes the sentence describing it.

Figure notes are removed. Where a note carried something the prose did not
already say, the sentence is folded into the paragraph beside it.
"""
import json, re, collections

ch4 = json.load(open('v6/ch4.json'))
T = {t['num']: t for t in json.load(open('v6/tables_final.json'))}
varmap = json.load(open('v6/varmap.json'))
dup = json.load(open('v6/dupes.json'))

sig_vars = {d['var'] for d in dup if d['sig']}
fig_vars = {d['var'] for d in dup if not d['sig']} - sig_vars
drop_figs = {d['fig'] for d in dup if d['var'] in sig_vars}

# ------------------------------------------------- 1. thin or drop the tables
blocks = collections.OrderedDict()
for n, t in T.items():
    bl = []
    for r in t['rows']:
        s = str(r[0])
        if s.startswith('__BLOCK__'):
            bl.append((s[9:], varmap.get(s[9:])))
    blocks[n] = bl

drop_tables, thin_tables = set(), {}
for n, bl in blocks.items():
    if not bl:
        continue
    gone = [b for b in bl if b[1] in fig_vars]
    if not gone:
        continue
    if len(gone) == len(bl):
        drop_tables.add(n)
    else:
        thin_tables[n] = {b[0] for b in gone}

# the figure that replaces each dropped table
tab2fig = {}
for d in dup:
    if d['var'] in fig_vars:
        for tn in d['tables']:
            if tn in drop_tables:
                tab2fig[tn] = d['fig']

new_tables = []
for t in json.load(open('v6/tables_final.json')):
    n = t['num']
    if n in drop_tables:
        continue
    if n in thin_tables:
        kill = thin_tables[n]
        rows, dropping = [], False
        for r in t['rows']:
            s = str(r[0])
            if s.startswith('__BLOCK__'):
                dropping = s[9:] in kill
                if dropping:
                    continue
            elif dropping:
                continue
            rows.append(r)
        t = dict(t, rows=rows)
    new_tables.append(t)

# ------------------------------- 2. rebuild Chapter Four in document order
# The chapter is laid out as TABLE -> paragraph -> FIGURE. Dropping a table
# leaves paragraph -> FIGURE, and the paragraph is re-pointed at the figure that
# now follows it. Nothing is moved, so the order of the figures is untouched.
out = [b for b in ch4
       if not (b['k'] == 'fig' and b['n'] in drop_figs)
       and not (b['k'] == 'table' and b['n'] in drop_tables)]

# ---------------------------------------------- 3. renumber, keeping a map
old_t = [b['n'] for b in out if b['k'] == 'table']
old_f = [b['n'] for b in out if b['k'] == 'fig']
tmap = {o: i + 1 for i, o in enumerate(old_t)}
fmap = {o: i + 5 for i, o in enumerate(old_f)}       # figures 1-4 are in Ch1-3

# what each ORIGINAL table number became: a table, or the figure that replaced it
ident = {}
for o in old_t:
    ident[o] = ('T', tmap[o])
for o, f in tab2fig.items():
    if f in fmap:
        ident[o] = ('F', fmap[f])

for b in out:
    if b['k'] == 'table':
        b['n'] = tmap[b['n']]
    elif b['k'] == 'fig':
        b['n'] = fmap[b['n']]
for t in new_tables:
    t['num'] = tmap[t['num']]

# ------------------------------------------- 4. re-point the prose
def name(old):
    k, n = ident[old]
    return f'{"Table" if k == "T" else "Figure"} {n}'

def join(names):
    """Render a mixed list of exhibits, collapsing consecutive runs."""
    def runs(nums):
        nums = sorted(set(nums)); out = []; i = 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            out.append((nums[i], nums[j])); i = j + 1
        return out

    parts = []
    for label, group in (('Table', [n for n in names if n[0] == 'T']),
                         ('Figure', [n for n in names if n[0] == 'F'])):
        nums = [n[1] for n in group]
        if not nums:
            continue
        rr = runs(nums)
        chunks = [str(a) if a == b else (f'{a} and {b}' if b == a + 1 else f'{a} to {b}')
                  for a, b in rr]
        plural = len(nums) > 1
        head = label + ('s' if plural else '')
        if len(chunks) == 1:
            parts.append(f'{head} {chunks[0]}')
        elif len(chunks) == 2:
            parts.append(f'{head} {chunks[0]} and {chunks[1]}')
        else:
            parts.append(f'{head} {", ".join(chunks[:-1])} and {chunks[-1]}')
    return ' and '.join(parts)

# One pass over both forms, so a replacement is never re-matched by the next
# pattern: writing "Table 16" for an old "Tables 21 and 22" must not then be
# read as old Table 16.
REF = re.compile(r'\bTables\s+(\d+)\s*(?:to|and|\u2013|-)\s*(\d+)|\bTable\s+(\d+)\b')

def fix(text):
    def sub(m):
        if m.group(3):
            o = int(m.group(3))
            return name(o) if o in ident else m.group(0)
        a, z = int(m.group(1)), int(m.group(2))
        covered = [o for o in range(a, z + 1) if o in ident]
        return join([ident[o] for o in covered]) if covered else m.group(0)
    return REF.sub(sub, text)

for b in out:
    if b['k'] in ('p', 'bul', 'num', 'h1', 'h2', 'h3', 'h4'):
        b['t'] = fix(b['t'])

# a sentence that now opens "Figure 8 shows" must not also say "As shown in"
for b in out:
    if b['k'] == 'p':
        b['t'] = re.sub(r'^As shown in (Figure \d+),\s*', r'\1 shows that ', b['t'])

# --------------------------------- 5. drop figure notes, keeping their content
MECHANICAL = re.compile(
    r'^(Bars?|Segments?)\s+(show|sum)[^.]*\.\s*', re.I)
folded = 0
for i, b in enumerate(out):
    if b['k'] != 'fig':
        continue
    note = b.pop('note', '') or ''
    rest = MECHANICAL.sub('', note).strip()
    if not rest:
        continue
    nxt = next((x for x in out[i + 1:i + 4] if x['k'] == 'p'), None)
    prv = next((x for x in reversed(out[max(0, i - 3):i]) if x['k'] == 'p'), None)
    target = nxt or prv
    if target is None:
        continue
    key = re.sub(r'[^a-z ]', '', rest.lower()).split()
    body = re.sub(r'[^a-z ]', '', (target['t']).lower())
    # already said?
    if key and sum(1 for w in key if w in body) / len(key) > 0.75:
        continue
    target['t'] = target['t'].rstrip() + ' ' + rest
    folded += 1

json.dump(out, open('v6/ch4.json', 'w'), ensure_ascii=False, indent=1)
json.dump(new_tables, open('v6/tables_final.json', 'w'), ensure_ascii=False, indent=1)

print(f'figures dropped (their variable is significant, the table keeps it): {len(drop_figs)}')
print(f'tables dropped (their content is now a figure)                    : {len(drop_tables)}')
print(f'tables thinned by one block                                       : {len(thin_tables)}')
print(f'note sentences folded into the prose                              : {folded}')
print(f'RESULT  tables {len(T)} -> {len(new_tables)}   figures {len(old_f) + len(drop_figs)} -> {len(old_f)}')
