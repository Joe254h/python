# -*- coding: utf-8 -*-
"""Reference-list repairs on the assembled thesis.

1. Restore into Chapters Two and Three two citations that draft 10 carried and
   the rebuild dropped, at the same claims draft 10 attached them to.
2. Resolve bare Mirera (2014) to the lettered entry.
3. Put the non-APA entries into APA 7 author-date form, using only the
   bibliographic detail already present in the entry.
4. Remove entries that no chapter cites, because APA 7 reserves the reference
   list for works actually cited.
5. Re-sort the list alphabetically.
"""
import docx, re

DOC = 'v6/thesis.docx'
d = docx.Document(DOC)
ps = d.paragraphs

from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

def retext(p, t):
    """Replace a paragraph's whole text, including any hyperlink runs, which
    python-docx does not expose through p.runs."""
    el = p._p
    runs = el.findall(qn('w:r'))
    links = el.findall(qn('w:hyperlink'))
    if not runs and not links:
        return False
    # keep the first run's formatting as the template
    if runs:
        tmpl = copy.deepcopy(runs[0])
    else:
        inner = links[0].findall(qn('w:r'))
        tmpl = copy.deepcopy(inner[0]) if inner else OxmlElement('w:r')
    for child in runs + links:
        el.remove(child)
    for old in tmpl.findall(qn('w:t')):
        tmpl.remove(old)
    # a hyperlink run carries the blue underlined style; drop it
    rPr = tmpl.find(qn('w:rPr'))
    if rPr is not None:
        for tag in ('w:color', 'w:u', 'w:rStyle'):
            for e in rPr.findall(qn(tag)): rPr.remove(e)
        c = OxmlElement('w:color'); c.set(qn('w:val'), '000000'); rPr.append(c)
    tn = OxmlElement('w:t'); tn.set(qn('xml:space'), 'preserve'); tn.text = t
    tmpl.append(tn)
    el.append(tmpl)
    return True

# ---------------------------------------------------------- 1. restore cites
EDITS = [
 ('Analysis in IBM SPSS Statistics',
  'Analysis in IBM SPSS Statistics',
  'Analysis in IBM SPSS Statistics (IBM Corp., 2017)'),
 ('Value-chain concepts are used as a mapping device',
  'Livelihood research provides background for interpreting education, experience, '
  'finance and collective membership,',
  'Livelihood research, in particular the sustainable livelihoods framework of '
  'Allison and Ellis (2001), provides background for interpreting education, '
  'experience, finance and collective membership,'),
 ('The target population comprised mud crab fishers',
  'The target population comprised mud crab fishers, middlemen, hoteliers and '
  'exporters operating in Kwale County.',
  'A target population comprises every individual able to give responses pertinent '
  'to the objectives of a study (Lamm & Lamm, 2019). The target population here '
  'comprised mud crab fishers, middlemen, hoteliers and exporters operating in '
  'Kwale County.'),
]
n = 0
for opener, old, new in EDITS:
    for p in ps:
        t = p.text.strip()
        if t.startswith(opener) and old in t:
            if retext(p, t.replace(old, new)): n += 1
            break
print('citations restored in Chapters Two and Three:', n)

# Gill (2010) has no reference entry and could not be verified; Yamane (1967),
# which is in the list, already carries the formula. The text sits inside a
# content control, so it is edited at the XML level.
g = 0
for t_el in d.element.body.iter(qn('w:t')):
    if t_el.text and 'Gill, 2010' in t_el.text:
        t_el.text = (t_el.text.replace('(Yamane, 1967; Gill, 2010)', '')
                               .replace('; Gill, 2010', '')).strip()
        g += 1
for t_el in d.element.body.iter(qn('w:t')):
    if t_el.text and 'Using Yamane\u2019s formula (Yamane, 1967) for sample size' in t_el.text:
        t_el.text = t_el.text.replace(
            'Using Yamane\u2019s formula (Yamane, 1967) for sample size determination',
            'Using Yamane\u2019s formula for sample size determination (Yamane, 1967)')
        g += 1
print('unverifiable Gill (2010) citation removed:', g)

# ------------------------------------------ 2. bare Mirera (2014) -> 2014a
m = 0
for p in ps:
    t = p.text
    t2 = re.sub(r'Mirera,\s*2014(?![ab])', 'Mirera, 2014a', t)
    t2 = re.sub(r'Mirera\s*\(2014\)(?![ab])', 'Mirera (2014a)', t2)
    if t2 != t and retext(p, t2): m += 1
print('bare Mirera (2014) citations lettered:', m)

# ------------------------------------------ 3. APA 7 form, detail preserved
APA = {
 'Fisheries Management and Development Act':
   'Fisheries Management and Development Act, No. 35 of 2016 (Kenya). '
   'http://faolex.fao.org/docs/pdf/ken160880.pdf',
 'Forest Conservation and Management Act':
   'Forest Conservation and Management Act, No. 34 of 2016 (Kenya). '
   'http://faolex.fao.org/docs/pdf/ken160882.pdf',
 'Kamata E.L.':
   'Kamata, E. L., Lamtane, H. A., & Abdalla, J. M. (2013). The impact of climate '
   'change on mud crab fishery and fattening to the community’s livelihood in Pangani '
   'and Rufiji estuaries in Tanzania. Department of Forest Economics, Sokoine '
   'University of Agriculture, Morogoro, Tanzania.',
 'Ladra FD':
   'Ladra, F. D., & Lin, C. J. (1991). Trade and marketing practices of mud crab in '
   'the Philippines. BOBP/REP, 51, 211–221.',
 'Ogawa, C. Y., K. Hamasaki':
   'Ogawa, C. Y., Hamasaki, K., Dan, S., & Kitada, S. (2011). Fishery biology of mud '
   'crabs Scylla spp. at Iriomote Island, Japan: Species composition, catch, growth '
   'and size at sexual maturity. Fisheries Science, 77, 915–927.',
 'Rahman M, Islam MA':
   'Rahman, M., Islam, M. A., Haque, S. M., & Wahab, M. (2017). Mud crab aquaculture '
   'and fisheries in coastal Bangladesh. World Aquaculture, 48, 47–52.',
 'Mirera OD (2011b)':
   'Mirera, D. O. (2011). Trends in exploitation, development and management of '
   'artisanal mud crab (Scylla serrata, Forsskal 1775) fishery and small-scale culture '
   'in Kenya: An overview. Ocean & Coastal Management, 54, 844–855.',
 'Mirera OD, Mosknes PO':
   'Mirera, D. O., & Moksnes, P. O. (2015). Comparative performance of wild juvenile '
   'Scylla serrata (Forsskål) in different culture systems: Net cages, mangrove pens '
   'and earthen ponds. Aquaculture International, 23, 155–173.',
 'Mirera OD, Ochiewo J':
   'Mirera, D. O., Ochiewo, J., Munyi, F., & Muriuki, T. (2013). Heredity or '
   'traditional knowledge: Fishing tactics and dynamics of artisanal mangrove crab '
   '(Scylla serrata) fishery. Ocean & Coastal Management, 84, 119–129.',
 'Giasuddin M Alam MF':
   'Giasuddin, M., & Alam, M. F. (1991). The mud crab (Scylla serrata) fishery and its '
   'bio-economics in Bangladesh. In C. A. Angel (Ed.), The mud crab: A report on the '
   'seminar convened in Surat Thani, Thailand, 5–8 November 1991 (pp. 29–40).',
 'Ludwig D, Hilborn R':
   'Ludwig, D., Hilborn, R., & Walters, C. (1993). Uncertainty, resource exploitation '
   'and conservation: Lessons from history. Science, 260, 17–36.',
 'Petersen EH':
   'Petersen, E. H., Suc, N. X., Thanh, D. V., & Hien, T. T. (2011). Bioeconomic '
   'analysis of extensive mud crab farming in Vietnam and improved diets. Aquaculture '
   'Economics & Management, 15, 83–102.',
 'Ochiewo J (2006)':
   'Ochiewo, J. (2006). Harvesting and sustainability of marine fisheries in '
   'Malindi–Ungwana Bay, northern Kenya coast (Final report, WIOMSA MARG 1).',
 'Keenan, C. P., Davie':
   'Keenan, C. P., Davie, P. J. F., & Mann, D. L. (1998). A revision of the genus '
   'Scylla De Haan, 1833 (Crustacea: Decapoda: Brachyura: Portunidae). Raffles '
   'Bulletin of Zoology, 46, 217–245.',
 'Mwaluma, J. (2002)':
   'Mwaluma, J. (2002). Pen culture of the mud crab Scylla serrata in Mtwapa mangrove '
   'system, Kenya. Western Indian Ocean Journal of Marine Science, 1, 127–133.',
 'Fulanda BC':
   'Fulanda, B. C., Munga, C., Ohtomi, J., Osore, M., Mugo, R., & Hossain, M. Y. '
   '(2009). The structure and evolution of the coastal migrant fishery of Kenya. '
   'Ocean & Coastal Management, 52, 459–466.',
 'Moser S, Macintosh D':
   'Moser, S., Macintosh, D., Laoprasert, S., & Tongdee, N. (2005). Population ecology '
   'of the mud crab Scylla olivacea: A study in the Andaman Sea, Satun Province, '
   'southern Thailand. Fisheries Research, 71, 27–41.',
 'Ochiewo J, De La Torre-Castro':
   'Ochiewo, J., De La Torre-Castro, M., Muthama, C., Munyi, F., & Nthuta, J. M. '
   '(2010). Socioeconomic features of sea cucumber fisheries in southern coast of '
   'Kenya. Ocean & Coastal Management, 53, 192–202.',
 'Richmond MD':
   'Richmond, M. D., Mohamed, A., De Villiers, A. K., Esseen, M., & Levay, L. (2006). '
   'Smallholder fisheries enterprises trials, Rufiji District, Tanzania. Rufiji '
   'Environment Management Project.',
 'I.B.M. Corp.':
   'IBM Corp. (2017). IBM SPSS Statistics for Windows. IBM Corp.',
 'Mwaluma, J. (2003)':
   'Mwaluma, J. (2003). Culture experiment on the growth and production of mud crabs, '
   'mullets, milkfish and prawns in the Mtwapa mangrove system, Kenya (Final report, '
   'WIOMSA MARG 1).',
}
ri = [i for i, p in enumerate(ps) if p.text.strip() == 'REFERENCES'][-1]
ai = next(i for i, p in enumerate(ps[ri:], ri) if p.text.strip() == 'APPENDICES')
fixed = 0
for p in ps[ri + 1:ai]:
    t = re.sub(r'\s+', ' ', p.text.strip())
    for key, apa in APA.items():
        if t.startswith(key):
            if retext(p, apa): fixed += 1
            break
print('reference entries put into APA 7 author-date form:', fixed)
d.save(DOC)

# ------------------------------------------ 4-5. keep only cited, then sort
d = docx.Document(DOC)
ps = d.paragraphs
ri = [i for i, p in enumerate(ps) if p.text.strip() == 'REFERENCES'][-1]
ai = next(i for i, p in enumerate(ps[ri:], ri) if p.text.strip() == 'APPENDICES')
body = '\n'.join(p.text for p in ps[:ri])
keep, drop = [], []
for p in ps[ri + 1:ai]:
    t = re.sub(r'\s+', ' ', p.text.strip())
    if len(t) <= 30: continue
    m1 = re.match(r'^([A-Z][\w’\'\-\.]{2,})', t)
    y = re.search(r'\((\d{4}[a-z]?)\)', t) or re.search(r'\b(\d{4}[a-z]?)\b', t)
    if not (m1 and y):
        keep.append(t); continue
    s, yy = m1.group(1).rstrip('.'), y.group(1)
    if re.search(re.escape(s) + r'[^)\n]{0,70}' + re.escape(yy), body):
        keep.append(t)
    else:
        drop.append(t)
print(f'\nreference entries cited in the text: {len(keep)}   never cited: {len(drop)}')
for t in drop: print('   removed:', t[:92])

def sortkey(t):
    a = re.sub(r'[^a-z ]', '', t.split('(')[0].lower()).strip()
    y = re.search(r'\((\d{4}[a-z]?)\)', t)
    return (a, y.group(1) if y else '')
final = sorted(set(keep), key=sortkey)
slots = [p for p in ps[ri + 1:ai] if len(p.text.strip()) > 30]
for i, p in enumerate(slots):
    if i < len(final): retext(p, final[i])
    else: p._p.getparent().remove(p._p)
d.save(DOC)
print(f'\nreference list rewritten: {len(final)} entries, alphabetical')
