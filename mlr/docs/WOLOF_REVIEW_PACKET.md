# Wolof native-review packet

**Status: nothing here is validated. None of it may be trained on or evaluated
against until a native Wolof speaker has been through it.**

Everything below was produced by a language model (me). It is drafted in the
official Senegalese orthography (`ë`, `ñ`, `ŋ`, `à`), but the orthography, the
word choices and the register all need a native speaker's judgement.

## What we need from you

For each item, three questions:

1. **Is it correct?** Does the Wolof say what the English says? Errors in the
   reasoning steps matter more than errors in the final sentence -- the whole
   point of this dataset is the reasoning.
2. **Is it natural?** Would a Wolof speaker explaining this to a friend
   actually put it this way, or does it read as translated French?
3. **Is the flagged choice right?** Each item lists the specific words I am
   unsure about. Those are where I would put your time first.

Corrections can be written straight into the "correction" line. If an item is
beyond repair, mark it `REJECT` -- a rejected item is far more useful to us
than a patched-up one, and the protocol here is quality over quantity.

---

## Decision 1 (blocking): how much French belongs in Wolof reasoning?

This one decision changes both the dataset and the way the model is scored, so
it needs settling before the rest of the review is worth doing.

Wolof speakers routinely count and do arithmetic in French. Wolof has its own
numerals (`benn, ñaar, ñett, ñeent, juróom, fukk`, and the quinary forms above
five), but in ordinary speech -- especially prices, measurements and mental
arithmetic -- French numerals are extremely common.

That leaves three options for the reasoning traces:

| option | what a trace looks like | risk |
|---|---|---|
| **A. Natural** | Wolof grammar, French numerals and technical loanwords wherever a speaker would use them | The model learns real Wolof, but "answers in Wolof" gets harder to measure automatically |
| **B. Purist** | Wolof numerals and Wolof coinages throughout | Clean to measure, but may teach a register no one actually speaks |
| **C. Split** | Natural in the reasoning block, Wolof-dominant in the final answer | Closest to real usage, but the two halves are trained on inconsistent conventions |

This is not only a linguistic question, it decides an evaluation threshold.
The evaluation flags a Wolof response as "collapsed into another language"
when the French share passes `WOLOF_FRENCH_TOLERANCE` (currently a placeholder
of 40%). Choose A and the threshold has to be loose, which risks letting real
collapse pass as natural code-switching. Choose B and it can be tight, but the
metric will punish Wolof that is perfectly normal.

**What we need:** which option, and roughly what share of French in a Wolof
reasoning trace should count as still-Wolof rather than a collapse.

---

## Decision 2: orthography

These drafts use official Senegalese orthography. Much Wolof written online
uses French-influenced spelling instead (`gni` for `ñu`, `kh` for `x`). Which
convention should the model be trained to produce? If learners and everyday
readers are the audience, the answer may not be the official one.

---

## Part 1 -- training sample (20 items)

### 1. `rice-01`  (arithmetic)

**English source question:** A shop buys 4 sacks of rice, each 25 kg. It sells 30 kg. How many kilograms are left?

**Wolof question:** Butig bi jënd na 4 sak ceeb, ku nekk 25 kilo. Jaay na 30 kilo. Ñaata kilo a des?

**English reasoning:** First I find the total bought: 4 sacks of 25 kg each is 4 x 25 = 100 kg. Then I subtract what was sold: 100 - 30 = 70. So 70 kg remain.

**Wolof reasoning:** Bu njëkk dama war a xam lu ñu jënd lépp: 4 sak yu 25 kilo mooy 4 x 25 = 100 kilo. Ba noppi ma bàyyi li ñu jaay: 100 - 30 = 70. Kon 70 kilo a des.

**Wolof answer:** 70 kilo a des.

*Measured French share of the reasoning: 12%*

**Specific points I am unsure about:**
- 'sak' vs 'saak' for sack
- 'butig' for shop
- 'a des' for 'remain'

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 2. `taxi-02`  (division)

**English source question:** Three friends share a taxi that costs 1800 francs equally. How much does each pay?

**Wolof question:** Ñett xarit séddoo nañu taksi bu jar 1800 franc ci yamale. Ñaata la ku nekk fay?

**English reasoning:** The fare is 1800 and there are 3 people sharing equally, so each pays 1800 / 3 = 600 francs.

**Wolof reasoning:** Njëg li mooy 1800 te 3 nit ñoo koy séddoo ci yamale, kon ku nekk day fay 1800 / 3 = 600 franc.

**Wolof answer:** Ku nekk day fay 600 franc.

*Measured French share of the reasoning: 6%*

**Specific points I am unsure about:**
- 'séddoo' (share among themselves) vs 'séddale'
- 'xarit' plural marking

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 3. `change-03`  (arithmetic)

**English source question:** Aissatou buys goods for 1750 francs and pays with 2000 francs. How much change does she get?

**Wolof question:** Aissatou jënd na marsandiis yu jar 1750 franc te fey na 2000 franc. Ñaata weccit la am?

**English reasoning:** She pays 2000 and the goods cost 1750. The change is 2000 - 1750 = 250 francs.

**Wolof reasoning:** Dafa fey 2000 te marsandiis yi jar nañu 1750. Weccit li mooy 2000 - 1750 = 250 franc.

**Wolof answer:** Weccit li mooy 250 franc.

*Measured French share of the reasoning: 0%*

**Specific points I am unsure about:**
- 'weccit' for change/coins
- 'marsandiis' loanword vs a Wolof term

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 4. `eggs-04`  (arithmetic)

**English source question:** A farmer has 6 hens. Each lays 4 eggs per week. How many eggs in 3 weeks?

**Wolof question:** Beykat bi am na 6 ginaar. Ku nekk day nqar 4 nen ci ayubés bu nekk. Ñaata nen ci 3 ayubés?

**English reasoning:** In one week the hens lay 6 x 4 = 24 eggs. Over 3 weeks that is 24 x 3 = 72 eggs.

**Wolof reasoning:** Ci benn ayubés ginaar yi dañuy nqar 6 x 4 = 24 nen. Ci 3 ayubés mooy 24 x 3 = 72 nen.

**Wolof answer:** 72 nen.

*Measured French share of the reasoning: 15%*

**Specific points I am unsure about:**
- 'nqar' for 'lay (an egg)' -- likely wrong, needs the correct verb
- 'ayubés' for week

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 5. `books-05`  (arithmetic)

**English source question:** A class of 28 pupils needs 3 books each. The school has 60 books. How many more are needed?

**Wolof question:** Klaas bu am 28 ndongo soxla na 3 téere ku nekk. Ekool bi am na 60 téere. Ñaata téere a ñu soxla ci kaw?

**English reasoning:** Total books needed: 28 x 3 = 84. The school already has 60, so it needs 84 - 60 = 24 more.

**Wolof reasoning:** Téere yi ñu soxla lépp: 28 x 3 = 84. Ekool bi am na ba tey 60, kon dafa soxla 84 - 60 = 24 yu yokk.

**Wolof answer:** 24 téere a ñu soxla ci kaw.

*Measured French share of the reasoning: 10%*

**Specific points I am unsure about:**
- 'ci kaw' vs 'yu yokk' for 'more/additional'
- 'soxla' construction with a number

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 6. `temp-06`  (arithmetic)

**English source question:** At noon the temperature is 34 degrees. By evening it has dropped by 9 degrees. What is the evening temperature?

**Wolof question:** Ci digg-bëccëg tàngoor bi mooy 34 degre. Ba ci ngoon wàcc na 9 degre. Ñaata degre la tàngoor bi ci ngoon?

**English reasoning:** The temperature starts at 34 and falls by 9, so the evening value is 34 - 9 = 25 degrees.

**Wolof reasoning:** Tàngoor bi dafa tàmbali ci 34 te wàcc 9, kon ci ngoon mooy 34 - 9 = 25 degre.

**Wolof answer:** 25 degre.

*Measured French share of the reasoning: 18%*

**Specific points I am unsure about:**
- 'tàngoor' for temperature
- 'digg-bëccëg' for noon

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 7. `cloth-07`  (division)

**English source question:** A tailor has 12 metres of cloth. Each dress needs 2.5 metres. How many complete dresses can he make?

**Wolof question:** Ñawkat bi am na 12 metar sér. Rob bu nekk soxla na 2.5 metar. Ñaata rob yu mat la mën a defar?

**English reasoning:** Divide the cloth by the amount per dress: 12 / 2.5 = 4.8. Only complete dresses count, so he can make 4, using 10 metres and leaving 2 metres over.

**Wolof reasoning:** Damay séddale sér bi ak li rob bu nekk soxla: 12 / 2.5 = 4.8. Rob yu mat rekk lañuy waññ, kon mën na defar 4, jëfandikoo 10 metar te bàyyi 2 metar.

**Wolof answer:** Mën na defar 4 rob yu mat.

*Measured French share of the reasoning: 14%*

**Specific points I am unsure about:**
- decimal 2.5 read aloud in Wolof -- comma or point, and is it read in French?
- 'ñawkat' for tailor
- 'waññ' for count

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 8. `savings-08`  (arithmetic)

**English source question:** Mariama saves 500 francs every week for 8 weeks. How much has she saved?

**Wolof question:** Mariama dafay denc 500 franc ayubés bu nekk diirub 8 ayubés. Ñaata la denc?

**English reasoning:** She saves the same amount each week, so the total is 500 x 8 = 4000 francs.

**Wolof reasoning:** Dafay denc xaalis bu yam ayubés bu nekk, kon lépp mooy 500 x 8 = 4000 franc.

**Wolof answer:** Denc na 4000 franc.

*Measured French share of the reasoning: 14%*

**Specific points I am unsure about:**
- 'denc' for save money
- 'diirub' for 'for a duration of'

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 9. `journey-09`  (arithmetic)

**English source question:** A driver travels 45 km, rests, then travels 38 km more. What is the total distance?

**Wolof question:** Sofër bi dox na 45 kilomet, noppalu, ba noppi dox 38 kilomet yu yokk. Ñaata kilomet la lépp?

**English reasoning:** The two legs add together: 45 + 38 = 83 km. The rest does not change the distance.

**Wolof reasoning:** Ñaari yoon yi dañuy boole: 45 + 38 = 83 kilomet. Noppalu du soppi yoon wi.

**Wolof answer:** Lépp mooy 83 kilomet.

*Measured French share of the reasoning: 8%*

**Specific points I am unsure about:**
- 'noppalu' for rest
- 'boole' for add together

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 10. `discount-10`  (percentage)

**English source question:** A radio costs 4000 francs. There is a 25% discount. What is the new price?

**Wolof question:** Rajo bi jar na 4000 franc. Am na wàññi bu tollu ci 25%. Ñaata la njëg bu bees bi?

**English reasoning:** 25% of 4000 is 4000 x 25 / 100 = 1000. Subtracting the discount: 4000 - 1000 = 3000 francs.

**Wolof reasoning:** 25% ci 4000 mooy 4000 x 25 / 100 = 1000. Bu ma bàyyee wàññi bi: 4000 - 1000 = 3000 franc.

**Wolof answer:** Njëg bu bees bi mooy 3000 franc.

*Measured French share of the reasoning: 17%*

**Specific points I am unsure about:**
- 'wàññi' for discount/reduction
- how percentages are normally spoken in Wolof

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 11. `bottles-11`  (arithmetic)

**English source question:** There are 7 boxes of soda, each holding 24 bottles. How many bottles in total?

**Wolof question:** Am na 7 kees sooda, ku nekk am 24 buteel. Ñaata buteel a am lépp?

**English reasoning:** Each box has the same number of bottles, so I multiply: 7 x 24 = 168 bottles.

**Wolof reasoning:** Kees bu nekk am na limu buteel bu yam, kon damay wutal: 7 x 24 = 168 buteel.

**Wolof answer:** 168 buteel.

*Measured French share of the reasoning: 0%*

**Specific points I am unsure about:**
- 'wutal' for multiply -- is there a settled arithmetic verb?
- 'kees' for box/crate

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 12. `seedlings-12`  (arithmetic)

**English source question:** A garden has 6 rows of 9 seedlings. 5 seedlings died. How many are left?

**Wolof question:** Tool bi am na 6 rëdd yu am 9 garab yu ndaw. 5 ci ñoom dee nañu. Ñaata a des?

**English reasoning:** Total planted: 6 x 9 = 54 seedlings. Then 5 died, so 54 - 5 = 49 remain.

**Wolof reasoning:** Li ñu ji lépp: 6 x 9 = 54 garab. Ba noppi 5 dee nañu, kon 54 - 5 = 49 a des.

**Wolof answer:** 49 a des.

*Measured French share of the reasoning: 20%*

**Specific points I am unsure about:**
- 'garab yu ndaw' for seedling -- likely a better single term exists
- 'ji' for plant (verb)

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 13. `workday-13`  (time)

**English source question:** Aissatou works from 08:00 to 16:30 with a 45-minute break. How many minutes does she actually work?

**Wolof question:** Aissatou dafay liggéey la ko dale ci 08:00 ba 16:30, am 45 simili noppalu. Ñaata simili la liggéey dëgg-dëgg?

**English reasoning:** From 08:00 to 16:30 is 8 hours 30 minutes, which is 8 x 60 + 30 = 510 minutes. Removing the break: 510 - 45 = 465 minutes.

**Wolof reasoning:** La ko dale ci 08:00 ba 16:30 mooy 8 waxtu ak 30 simili, maanaam 8 x 60 + 30 = 510 simili. Bu ma bàyyee noppalu bi: 510 - 45 = 465 simili.

**Wolof answer:** Dafay liggéey 465 simili.

*Measured French share of the reasoning: 14%*

**Specific points I am unsure about:**
- 'simili' for minute vs the French 'minute'
- 'waxtu' for hour
- 'dëgg-dëgg' for 'actually'

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 14. `fish-14`  (arithmetic)

**English source question:** Fish costs 1200 francs per kilogram. How much do 3 kilograms cost?

**Wolof question:** Jën jar na 1200 franc ci kilo bu nekk. Ñaata la 3 kilo jar?

**English reasoning:** The price is per kilogram, so I multiply by the weight: 1200 x 3 = 3600 francs.

**Wolof reasoning:** Njëg li ci kilo la, kon damay wutal ak diis bi: 1200 x 3 = 3600 franc.

**Wolof answer:** 3600 franc.

*Measured French share of the reasoning: 8%*

**Specific points I am unsure about:**
- 'jën' for fish
- 'diis' for weight

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 15. `fees-15`  (arithmetic)

**English source question:** School fees are 15000 francs. A family has paid 9500 francs. How much is still owed?

**Wolof question:** Njëgu ekool bi mooy 15000 franc. Njaboot gi fey na 9500 franc. Ñaata la des ci fey?

**English reasoning:** Subtract what has been paid from the total: 15000 - 9500 = 5500 francs still owed.

**Wolof reasoning:** Damay bàyyi li ñu fey ci lépp: 15000 - 9500 = 5500 franc a des.

**Wolof answer:** 5500 franc a des ci fey.

*Measured French share of the reasoning: 31%*

**Specific points I am unsure about:**
- 'njaboot' for family
- 'des ci fey' for 'remains to be paid'

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 16. `schedule-16`  (logic)

**English source question:** Khady works on Monday and Wednesday. Ibrahima works on Tuesday and Thursday. Who works on Wednesday?

**Wolof question:** Khady dafay liggéey Altine ak Àllarba. Ibrahima dafay liggéey Talaata ak Alxames. Kan mooy liggéey Àllarba?

**English reasoning:** Khady's days are Monday and Wednesday. Ibrahima's days are Tuesday and Thursday. Wednesday appears only in Khady's list, so the answer is Khady.

**Wolof reasoning:** Bés yu Khady mooy Altine ak Àllarba. Yu Ibrahima mooy Talaata ak Alxames. Àllarba nekk na rekk ci bés yu Khady, kon tontu li mooy Khady.

**Wolof answer:** Khady

*Measured French share of the reasoning: 18%*

**Specific points I am unsure about:**
- day names Altine/Talaata/Àllarba/Alxames spelling

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 17. `unitprice-17`  (comparison)

**English source question:** A 2-litre bottle costs 900 francs. A 3-litre bottle costs 1200 francs. What is the price per litre of the cheaper option?

**Wolof question:** Buteel bu 2 liitar jar na 900 franc. Buteel bu 3 liitar jar na 1200 franc. Ñaata la liitar bi jar ci bi gëna yomb?

**English reasoning:** Price per litre for the first: 900 / 2 = 450. For the second: 1200 / 3 = 400. 400 is less than 450, so the 3-litre bottle is cheaper per litre, at 400 francs.

**Wolof reasoning:** Njëgu liitar ci bu njëkk bi: 900 / 2 = 450. Ci ñaareel bi: 1200 / 3 = 400. 400 dafa gëna tuuti 450, kon buteel bu 3 liitar bi mooy gëna yomb, ci 400 franc liitar bi.

**Wolof answer:** 400 franc liitar bi.

*Measured French share of the reasoning: 0%*

**Specific points I am unsure about:**
- 'yomb' for cheap
- 'ñaareel' for second (ordinal)
- 'gëna tuuti' for 'less than'

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 18. `calendar-18`  (time)

**English source question:** How many days are there from 10 May to 3 June?

**Wolof question:** Ñaata fan a am la ko dale ci 10 Me ba 3 Suwe?

**English reasoning:** May has 31 days, so from 10 May to 31 May is 31 - 10 = 21 days. Then add the 3 days of June: 21 + 3 = 24 days.

**Wolof reasoning:** Me am na 31 fan, kon la ko dale ci 10 Me ba 31 Me mooy 31 - 10 = 21 fan. Ba noppi ma yokk 3 fan yu Suwe: 21 + 3 = 24 fan.

**Wolof answer:** 24 fan.

*Measured French share of the reasoning: 5%*

**Specific points I am unsure about:**
- month names Me / Suwe -- French borrowings, confirm the usual written forms
- 'fan' for day vs 'bés'

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 19. `weights-19`  (arithmetic)

**English source question:** Three bags weigh 5 kg each and two bags weigh 8 kg each. What is the total weight?

**Wolof question:** Ñett mboot ku nekk diis na 5 kilo te ñaar mboot ku nekk diis na 8 kilo. Ñaata kilo la lépp diis?

**English reasoning:** The light bags weigh 3 x 5 = 15 kg. The heavy bags weigh 2 x 8 = 16 kg. Together that is 15 + 16 = 31 kg.

**Wolof reasoning:** Mboot yu woyof yi diis nañu 3 x 5 = 15 kilo. Mboot yu diis yi diis nañu 2 x 8 = 16 kilo. Boole ko mooy 15 + 16 = 31 kilo.

**Wolof answer:** Lépp diis na 31 kilo.

*Measured French share of the reasoning: 0%*

**Specific points I am unsure about:**
- 'woyof' for light (weight)
- using 'diis' as both noun and verb

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### 20. `instruct-20`  (instruction-following)

**English source question:** What is 17 + 25?

**Wolof question:** Ñaata la 17 + 25?

**English reasoning:** I add the units: 7 + 5 = 12, so I write 2 and carry 1. Then the tens: 1 + 2 + 1 = 4. That gives 42. The instruction says the answer must be the number alone.

**Wolof reasoning:** Damay boole yu ndaw yi: 7 + 5 = 12, ma bind 2 te yóbbu 1. Ba noppi fukk yi: 1 + 2 + 1 = 4. Loolu mooy joxe 42. Ndigal li nee na tontu li war na doon limu bi rekk.

**Wolof answer:** 42

*Measured French share of the reasoning: 0%*

**Specific points I am unsure about:**
- 'yóbbu' for 'carry' in addition
- 'ndigal' for instruction
- whether carrying is normally described in Wolof at all, or done in French

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

## Part 2 -- held-out evaluation questions (12 items)

These are the questions the model is *scored* on. A mistranslation
here produces a wrong score, which is worse than no score, so they
need the same scrutiny as the training data.

### `mango-01-wo`

**English:** A trader has 3 baskets. Each basket holds 12 mangoes. How many mangoes does she have in total?

**Wolof:** Jaaykat bi am na 3 pañe. Pañe bu nekk am na 12 mango. Ñaata mango la am lépp?

*(expected answer: 36)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `fare-02-wo`

**English:** A bus trip costs 250 francs one way. Ousmane travels to work and back every day for 5 days. How much does he spend in total?

**Wolof:** Nawlu bus bi 250 franc la ci yoon wu nekk. Ousmane dafay dem liggéey te dellu bés bu nekk, diirub 5 fan. Ñaata xaalis la jëfandikoo lépp?

*(expected answer: 2500)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `water-03-wo`

**English:** A bucket holds 8 litres of water. Fatou filled 3 buckets, then used 5 litres. How many litres are left?

**Wolof:** Benn seau am na 8 liitar ndox. Fatou feesal na 3 seau, ba noppi jëfandikoo 5 liitar. Ñaata liitar a ko des?

*(expected answer: 19)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `ages-04-wo`

**English:** Amina is 12 years old. Her brother is 3 years older than her. What is the sum of their ages?

**Wolof:** Amina am na 12 at. Magam dafa ko ëpp 3 at. Ñaata at la seen at yépp tolloo?

*(expected answer: 27)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `clock-05-wo`

**English:** The bus leaves at 07:45 and the journey takes 50 minutes. At what time does it arrive? Answer in HH:MM.

**Wolof:** Bus bi dafay dem ci 07:45 te yoon wi day jël 50 simili. Ci ban waxtu la ñëw? Tontu ci anam HH:MM.

*(expected answer: 08:35)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `pct-06-wo`

**English:** A school has 200 pupils. 45% of them are girls. How many girls are there?

**Wolof:** Ekool bi am na 200 ndongo. 45% ci ñoom ay janq lañu. Ñaata janq a am?

*(expected answer: 90)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `share-07-wo`

**English:** 4500 francs are shared equally among 6 people. How much does each person receive?

**Wolof:** Ñu séddale 4500 franc ci diggante 6 nit ci yamale. Ñaata la ku nekk am?

*(expected answer: 750)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `rate-08-wo`

**English:** Moussa walks 4 kilometres in 50 minutes. At the same pace, how many minutes does he need to walk 6 kilometres?

**Wolof:** Moussa dafay dox 4 kilomet ci 50 simili. Ci yoon wu yam, ñaata simili la war a jël ngir dox 6 kilomet?

*(expected answer: 75)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `chairs-09-wo`

**English:** A hall has 5 rows of 8 chairs. 3 chairs are broken. How many chairs are in good condition?

**Wolof:** Néeg bi am na 5 rëdd yu am 8 siis. 3 siis yaqu nañu. Ñaata siis a baax?

*(expected answer: 37)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `frac-10-wo`

**English:** Take half of 60, then take a third of that result. What is the result?

**Wolof:** Jël genn-wàll bu 60, ba noppi jël benn-ci-ñett bi ci njariñ bi. Lan mooy tontu li?

*(expected answer: 10)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `algebra-11-wo`

**English:** If x + 7 = 22, what is the value of x?

**Wolof:** Su x + 7 tollook 22, ñaata la x?

*(expected answer: 15)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---

### `order-12-wo`

**English:** Awa is taller than Fatou. Fatou is taller than Bineta. Who is the tallest?

**Wolof:** Awa dafa gëna gudd Fatou. Fatou dafa gëna gudd Bineta. Kan moo gëna gudd?

*(expected answer: Awa)*

- [ ] correct  - [ ] natural  - [ ] REJECT

**correction:**

---


## Sign-off

| reviewer | date | items reviewed | items rejected |
|---|---|---|---|
|  |  |  |  |

Once signed off, set `human_verified: true` for the reviewed rows in
`data/sample20/sample20.jsonl` and record the reviewer in
`data/sample20/PROVENANCE.md`. Until then every row stays `human_verified:
false`, and no Wolof number computed from this data should be reported as
final.
