import sys
sys.argv=['x']
exec(open('/tmp/claude-0/-home-user-python/920ad5d8-6e07-5909-9e17-40c3ac0fe128/scratchpad/add_who5.py').read().split('# ============================================================ NEW SECTION J')[0]
     .replace("SRC = ('/root/.claude/uploads/920ad5d8-6e07-5909-9e17-40c3ac0fe128/'\n       '3645ea1e-Trader_Questionnaire_Integrated_edited_final_final.docx')",
              "SRC = '/home/user/python/output/Trader_Questionnaire_FULL_v3.docx'")
     .replace("OUT = '/home/user/python/output/Trader_Questionnaire_with_Wellbeing.docx'",
              "OUT = '/home/user/python/output/Trader_Questionnaire_FULL_v4.docx'"))

n_before = len(_content(body))

h2('F0e.  Pilot revisions — read before fielding')
mynote('The pilot showed that on nine of the twelve cards we used, the cheaper option happened '
       'to be printed on the left. Traders chose the left-hand option 59% of the time, and '
       'once I allowed for that in the model the price effect reversed sign. I could not tell '
       'price and position apart. Four traders also chose the left option on every single '
       'card, which is not a choice, it is disengagement. The four changes below fix both '
       'problems. Items 1 to 3 must be built into the tablet form before the next interview.')

q('1.', 'ROTATE THE OPTIONS. For each card, the tablet must decide at random which of the two '
        'services is shown first. Do not always print the same one on the left.')
instr('If the form cannot randomise, alternate by respondent: odd IDs see the design order, '
      'even IDs see the two options swapped. Recording the order (item 2) is what matters most.')
q('2.', 'RECORD WHAT WAS SHOWN. For every card, store which service appeared in the first '
        'position.', '1 = design order (A first)    2 = swapped (B first)')
instr('Without this field the analysis cannot correct for position, and the full survey will '
      'have the same problem the pilot had.')
q('3.', 'RECORD THE BLOCK AS A CODE, not as text.', '1 = Block 1    2 = Block 2    3 = Block 3')
instr('The pilot stored this as "Block 1 (Odd-numbered IDs)". With three blocks the analysis '
      'needs a clean number.')
q('4.', 'FLAG STRAIGHT-LINING WHILE YOU ARE STILL WITH THE RESPONDENT. If the same position is '
        'chosen on all six cards, the form should prompt the enumerator.')
instr('Prompt to read: "Just to check — for each of these, would you like me to read the two '
      'options again?" Do not suggest an answer. Record the response in F11.')
mynote('I have also standardised the wording of the service descriptions. In the pilot the same '
       'option was written two ways on different cards — "Private operator" on one and "Private '
       'operator (Operator complaints)" on another — which would have been coded as two '
       'different things.')

new = _content(body)[n_before:]
target = None
for p in doc.paragraphs:
    if p.text.strip().startswith('Block 1'):
        target = p._p; break
assert target is not None
for el in new:
    body.remove(el); target.addprevious(el)

# extend the enumerator checks
anchor = None
for p in doc.paragraphs:
    if p.text.strip().startswith('F10.'):
        anchor = p._p; break
assert anchor is not None
n2 = len(_content(body))
q('F11.', 'Did the form flag this respondent for choosing the same position on every card?',
  '1 = Yes, and they reconsidered    2 = Yes, and they kept the same answers    3 = Not flagged')
instr('If 2, note it on the cover sheet. Their choice data is kept but marked, so the analysis '
      'can test whether excluding them changes the result.')
new2 = _content(body)[n2:]
cur = anchor
for el in new2:
    body.remove(el); cur.addnext(el); cur = el

doc.save(OUT)
print('saved', OUT)
