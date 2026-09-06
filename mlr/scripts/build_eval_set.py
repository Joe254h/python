#!/usr/bin/env python3
"""Emit the held-out evaluation set, four languages, one JSONL row per item.

Design notes that matter for interpreting any number this set produces:

* Gold answers are numeric wherever possible. A numeric gold is identical in
  all four languages, so `correct` measures reasoning and nothing else -- the
  language question is measured separately and must not leak into accuracy.
* Clock times are written in 24-hour digits on purpose. Traditional Swahili
  time runs six hours offset from the clock (saa moja = 7 a.m.), so a
  word-form time question would test cultural time convention rather than
  arithmetic, and would score Swahili unfairly.
* These items are HELD OUT. Nothing here may appear in the 20-example training
  sample, or the evaluation is worthless.
* Every Wolof string is flagged needs_native_review. The eval set needs native
  validation just as much as the training data does -- a mistranslated
  question produces a wrong score, and a wrong score is worse than no score.
"""

import json
from pathlib import Path

# id, answer_type, gold, domain, {lang: question}
ITEMS = [
    ("mango-01", "numeric", "36", "arithmetic", {
        "en": "A trader has 3 baskets. Each basket holds 12 mangoes. How many mangoes does she have in total?",
        "fr": "Une commerçante a 3 paniers. Chaque panier contient 12 mangues. Combien de mangues a-t-elle au total ?",
        "sw": "Mfanyabiashara ana vikapu 3. Kila kikapu kina maembe 12. Ana maembe mangapi kwa jumla?",
        "wo": "Jaaykat bi am na 3 pañe. Pañe bu nekk am na 12 mango. Ñaata mango la am lépp?",
    }),
    ("fare-02", "numeric", "2500", "arithmetic", {
        "en": "A bus trip costs 250 francs one way. Ousmane travels to work and back every day for 5 days. How much does he spend in total?",
        "fr": "Le trajet en bus coûte 250 francs par voyage. Ousmane va au travail et rentre chaque jour pendant 5 jours. Combien dépense-t-il au total ?",
        "sw": "Nauli ya basi ni faranga 250 kwa safari moja. Ousmane huenda kazini na kurudi kila siku kwa siku 5. Anatumia faranga ngapi kwa jumla?",
        "wo": "Nawlu bus bi 250 franc la ci yoon wu nekk. Ousmane dafay dem liggéey te dellu bés bu nekk, diirub 5 fan. Ñaata xaalis la jëfandikoo lépp?",
    }),
    ("water-03", "numeric", "19", "arithmetic", {
        "en": "A bucket holds 8 litres of water. Fatou filled 3 buckets, then used 5 litres. How many litres are left?",
        "fr": "Un seau contient 8 litres d'eau. Fatou a rempli 3 seaux, puis a utilisé 5 litres. Combien de litres lui reste-t-il ?",
        "sw": "Ndoo moja ina lita 8 za maji. Fatou alijaza ndoo 3, kisha akatumia lita 5. Amebakiwa na lita ngapi?",
        "wo": "Benn seau am na 8 liitar ndox. Fatou feesal na 3 seau, ba noppi jëfandikoo 5 liitar. Ñaata liitar a ko des?",
    }),
    ("ages-04", "numeric", "27", "arithmetic", {
        "en": "Amina is 12 years old. Her brother is 3 years older than her. What is the sum of their ages?",
        "fr": "Amina a 12 ans. Son frère a 3 ans de plus qu'elle. Quelle est la somme de leurs âges ?",
        "sw": "Amina ana miaka 12. Kaka yake ni mkubwa kwake kwa miaka 3. Jumla ya miaka yao ni ngapi?",
        "wo": "Amina am na 12 at. Magam dafa ko ëpp 3 at. Ñaata at la seen at yépp tolloo?",
    }),
    ("clock-05", "exact", "08:35", "time", {
        "en": "The bus leaves at 07:45 and the journey takes 50 minutes. At what time does it arrive? Answer in HH:MM.",
        "fr": "Le bus part à 07:45 et le trajet dure 50 minutes. À quelle heure arrive-t-il ? Réponds au format HH:MM.",
        "sw": "Basi linaondoka 07:45 na safari inachukua dakika 50. Litafika saa ngapi? Jibu kwa muundo HH:MM.",
        "wo": "Bus bi dafay dem ci 07:45 te yoon wi day jël 50 simili. Ci ban waxtu la ñëw? Tontu ci anam HH:MM.",
    }),
    ("pct-06", "numeric", "90", "percentage", {
        "en": "A school has 200 pupils. 45% of them are girls. How many girls are there?",
        "fr": "Une école compte 200 élèves. 45 % sont des filles. Combien y a-t-il de filles ?",
        "sw": "Shule ina wanafunzi 200. Asilimia 45 ni wasichana. Kuna wasichana wangapi?",
        "wo": "Ekool bi am na 200 ndongo. 45% ci ñoom ay janq lañu. Ñaata janq a am?",
    }),
    ("share-07", "numeric", "750", "division", {
        "en": "4500 francs are shared equally among 6 people. How much does each person receive?",
        "fr": "On partage 4500 francs également entre 6 personnes. Combien reçoit chaque personne ?",
        "sw": "Faranga 4500 zinagawanywa sawa kati ya watu 6. Kila mtu anapata faranga ngapi?",
        "wo": "Ñu séddale 4500 franc ci diggante 6 nit ci yamale. Ñaata la ku nekk am?",
    }),
    ("rate-08", "numeric", "75", "rate", {
        "en": "Moussa walks 4 kilometres in 50 minutes. At the same pace, how many minutes does he need to walk 6 kilometres?",
        "fr": "Moussa marche 4 kilomètres en 50 minutes. À la même allure, combien de minutes lui faut-il pour 6 kilomètres ?",
        "sw": "Moussa anatembea kilomita 4 kwa dakika 50. Kwa mwendo huo huo, atatumia dakika ngapi kutembea kilomita 6?",
        "wo": "Moussa dafay dox 4 kilomet ci 50 simili. Ci yoon wu yam, ñaata simili la war a jël ngir dox 6 kilomet?",
    }),
    ("chairs-09", "numeric", "37", "arithmetic", {
        "en": "A hall has 5 rows of 8 chairs. 3 chairs are broken. How many chairs are in good condition?",
        "fr": "Une salle a 5 rangées de 8 chaises. 3 chaises sont cassées. Combien de chaises sont en bon état ?",
        "sw": "Ukumbi una safu 5 za viti, kila safu ina viti 8. Viti 3 vimeharibika. Kuna viti vingapi vizuri?",
        "wo": "Néeg bi am na 5 rëdd yu am 8 siis. 3 siis yaqu nañu. Ñaata siis a baax?",
    }),
    ("frac-10", "numeric", "10", "fractions", {
        "en": "Take half of 60, then take a third of that result. What is the result?",
        "fr": "Prends la moitié de 60, puis le tiers du résultat. Quel est le résultat ?",
        "sw": "Chukua nusu ya 60, kisha uchukue theluthi ya jibu hilo. Jibu ni nini?",
        "wo": "Jël genn-wàll bu 60, ba noppi jël benn-ci-ñett bi ci njariñ bi. Lan mooy tontu li?",
    }),
    ("algebra-11", "numeric", "15", "algebra", {
        "en": "If x + 7 = 22, what is the value of x?",
        "fr": "Si x + 7 = 22, quelle est la valeur de x ?",
        "sw": "Ikiwa x + 7 = 22, thamani ya x ni ipi?",
        "wo": "Su x + 7 tollook 22, ñaata la x?",
    }),
    ("order-12", "exact", "Awa", "logic", {
        "en": "Awa is taller than Fatou. Fatou is taller than Bineta. Who is the tallest?",
        "fr": "Awa est plus grande que Fatou. Fatou est plus grande que Bineta. Qui est la plus grande ?",
        "sw": "Awa ni mrefu kuliko Fatou. Fatou ni mrefu kuliko Bineta. Ni nani mrefu zaidi?",
        "wo": "Awa dafa gëna gudd Fatou. Fatou dafa gëna gudd Bineta. Kan moo gëna gudd?",
    }),
]

LANGS = ("en", "fr", "sw", "wo")


def main() -> None:
    out = Path("data/eval/held_out_v1.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for base_id, atype, gold, domain, qs in ITEMS:
        for lang in LANGS:
            rows.append({
                "id": f"{base_id}-{lang}",
                "lang": lang,
                "question": qs[lang],
                "gold": gold,
                "answer_type": atype,
                "domain": domain,
                "needs_native_review": lang == "wo",
            })
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} items ({len(ITEMS)} problems x {len(LANGS)} languages) -> {out}")


if __name__ == "__main__":
    main()
