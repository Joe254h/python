# -*- coding: utf-8 -*-
"""Static check of the SPSS syntax: every command ends in a period, every
variable named exists in the .sav, and every table in the thesis is covered."""
import re, json, pyreadstat
sps = open('out/Mud_crab_BMU_analysis.sps').read()
_, meta = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')
names = set(meta.column_names) | {'n', 'ntot', 'pct', 'keep', 'figdat', 'crab'}

lines = sps.split('\n')
# strip comments
body, i = [], 0
for ln in lines:
    if ln.strip().startswith('*'): continue
    body.append(ln)
txt = '\n'.join(body)

# commands are separated by a period at end of line
cmds = [c.strip() for c in re.split(r'\.\s*\n', txt) if c.strip()]
KEY = ('GET', 'DATASET', 'CROSSTABS', 'FREQUENCIES', 'AGGREGATE', 'COMPUTE',
       'VARIABLE', 'FORMATS', 'EXECUTE', 'GRAPH', 'TEMPORARY', 'SELECT',
       'MEANS', 'NPAR', 'EXAMINE', 'USE', 'FILTER', 'DESCRIPTIVES')
bad = [c[:60] for c in cmds if not c.upper().startswith(KEY)]
print('commands:', len(cmds), '  not starting with a known keyword:', len(bad))
for b in bad: print('   ', b)

# unterminated: last non-empty line of the file must end with '.'
last = [l for l in lines if l.strip()][-1]
print('file ends with a period:', last.rstrip().endswith('.'))

# variables used
used = set(re.findall(r'\b([a-z][a-z0-9_]*_0_[123])\b', txt))
unknown = sorted(used - names)
print('variables referenced:', len(used), '  not in the .sav:', unknown)

# TEMPORARY must be immediately followed by SELECT IF
tmp = [i for i, l in enumerate(body) if l.strip() == 'TEMPORARY.']
bad2 = [i for i in tmp if not body[i+1].strip().startswith('SELECT IF')]
print('TEMPORARY blocks:', len(tmp), '  not followed by SELECT IF:', len(bad2))

# DATASET DECLARE / CLOSE balance
print('DATASET DECLARE:', txt.count('DATASET DECLARE'),
      ' DATASET CLOSE:', txt.count('DATASET CLOSE'))

# every thesis table named in the index
T = [t['num'] for t in json.load(open('v6/tables_final.json'))]
missing = [n for n in T if not re.search(rf'\* Table {n:>2}: ', sps)]
print('thesis tables listed in the index:', len(T) - len(missing), 'of', len(T),
      ('missing ' + str(missing)) if missing else '')

# every variable the thesis tables use appears in the syntax
varmap = json.load(open('v6/varmap.json'))
need = set()
for t in json.load(open('v6/tables_all.json')):
    for r in t['rows']:
        s = str(r[0])
        if s.startswith('__BLOCK__'):
            v = varmap.get(s[9:])
            if v: need.add(v)
gap = sorted(need - used)
print('variables reported in the thesis but absent from the syntax:', len(gap), gap)
