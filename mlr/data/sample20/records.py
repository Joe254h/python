# -*- coding: utf-8 -*-
"""The 20-example verified sample, in Swahili, Wolof, English and French.

PROVENANCE -- read before using any of this.

The upstream dataset (HuggingFaceH4/Multilingual-Thinking) could not be
downloaded: huggingface.co is blocked by this environment's egress policy.
So the English and French rows here are NOT upstream rows. They are authored
in the upstream schema and the upstream style (a developer/system constraint,
a user question, then a reasoning trace and a final answer) so that the
translation, verification and format tooling can be exercised and reviewed
now. Every record is marked `upstream_id: None` to keep that unambiguous.

When HF becomes reachable, scripts/ingest_upstream.py replaces these with real
rows; the Swahili and Wolof work here stays valid as a translation reference
and as the calibration set for the reviewers.

Verification vocabulary, used exactly:
  authored          written directly in this language, not translated
  model_translated  translated by a language model (me), unverified by a human
  model_checked     translated by me, then checked by me against an explicit
                    grammatical checklist -- this is NOT human verification
  human_verified    signed off by a native speaker. Nothing carries this yet.

Swahili is model_checked. Wolof is model_translated and must not ship until a
native Wolof speaker has reviewed it; each Wolof record carries `wo_review`
listing the specific choices I am unsure about, so review is targeted rather
than open-ended.
"""

# Applies to every record unless a record overrides it.
DEFAULT_STATUS = {
    "en": "authored",
    "fr": "authored",
    "sw": "model_checked",
    "wo": "model_translated",
}

SAMPLES = [
    dict(
        id="rice-01", domain="arithmetic", answer_type="numeric", gold="70",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A shop buys 4 sacks of rice, each 25 kg. It sells 30 kg. How many kilograms are left?",
            "fr": "Une boutique achète 4 sacs de riz de 25 kg chacun. Elle en vend 30 kg. Combien de kilogrammes restent ?",
            "sw": "Duka linanunua magunia 4 ya mchele, kila moja lina kilo 25. Linauza kilo 30. Zimebaki kilo ngapi?",
            "wo": "Butig bi jënd na 4 sak ceeb, ku nekk 25 kilo. Jaay na 30 kilo. Ñaata kilo a des?",
        },
        thinking={
            "en": "First I find the total bought: 4 sacks of 25 kg each is 4 x 25 = 100 kg. Then I subtract what was sold: 100 - 30 = 70. So 70 kg remain.",
            "fr": "D'abord je calcule le total acheté : 4 sacs de 25 kg font 4 x 25 = 100 kg. Ensuite je soustrais ce qui a été vendu : 100 - 30 = 70. Il reste donc 70 kg.",
            "sw": "Kwanza natafuta jumla iliyonunuliwa: magunia 4 ya kilo 25 kila moja ni 4 x 25 = 100 kilo. Kisha naondoa zilizouzwa: 100 - 30 = 70. Kwa hivyo zimebaki kilo 70.",
            "wo": "Bu njëkk dama war a xam lu ñu jënd lépp: 4 sak yu 25 kilo mooy 4 x 25 = 100 kilo. Ba noppi ma bàyyi li ñu jaay: 100 - 30 = 70. Kon 70 kilo a des.",
        },
        answer={
            "en": "70 kg are left.", "fr": "Il reste 70 kg.",
            "sw": "Zimebaki kilo 70.", "wo": "70 kilo a des.",
        },
        wo_review=["'sak' vs 'saak' for sack", "'butig' for shop", "'a des' for 'remain'"],
    ),
    dict(
        id="taxi-02", domain="division", answer_type="numeric", gold="600",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Three friends share a taxi that costs 1800 francs equally. How much does each pay?",
            "fr": "Trois amis partagent équitablement un taxi qui coûte 1800 francs. Combien paie chacun ?",
            "sw": "Teksi inagharimu faranga 1800. Marafiki watatu wanagawana gharama hiyo sawa. Kila mmoja analipa faranga ngapi?",
            "wo": "Ñett xarit séddoo nañu taksi bu jar 1800 franc ci yamale. Ñaata la ku nekk fay?",
        },
        thinking={
            "en": "The fare is 1800 and there are 3 people sharing equally, so each pays 1800 / 3 = 600 francs.",
            "fr": "Le tarif est de 1800 et 3 personnes partagent également, donc chacun paie 1800 / 3 = 600 francs.",
            "sw": "Nauli ni 1800 na kuna watu 3 wanaogawana sawa, kwa hivyo kila mmoja analipa 1800 / 3 = 600 faranga.",
            "wo": "Njëg li mooy 1800 te 3 nit ñoo koy séddoo ci yamale, kon ku nekk day fay 1800 / 3 = 600 franc.",
        },
        answer={
            "en": "Each pays 600 francs.", "fr": "Chacun paie 600 francs.",
            "sw": "Kila mmoja analipa faranga 600.", "wo": "Ku nekk day fay 600 franc.",
        },
        wo_review=["'séddoo' (share among themselves) vs 'séddale'", "'xarit' plural marking"],
    ),
    dict(
        id="change-03", domain="arithmetic", answer_type="numeric", gold="250",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Aissatou buys goods for 1750 francs and pays with 2000 francs. How much change does she get?",
            "fr": "Aissatou achète pour 1750 francs et paie avec 2000 francs. Combien reçoit-elle de monnaie ?",
            "sw": "Aissatou ananunua bidhaa kwa faranga 1750 na analipa kwa faranga 2000. Anapata chenji ya faranga ngapi?",
            "wo": "Aissatou jënd na marsandiis yu jar 1750 franc te fey na 2000 franc. Ñaata weccit la am?",
        },
        thinking={
            "en": "She pays 2000 and the goods cost 1750. The change is 2000 - 1750 = 250 francs.",
            "fr": "Elle paie 2000 et les marchandises coûtent 1750. La monnaie est 2000 - 1750 = 250 francs.",
            "sw": "Analipa 2000 na bidhaa zina gharama ya 1750. Chenji ni 2000 - 1750 = 250 faranga.",
            "wo": "Dafa fey 2000 te marsandiis yi jar nañu 1750. Weccit li mooy 2000 - 1750 = 250 franc.",
        },
        answer={
            "en": "She gets 250 francs in change.", "fr": "Elle reçoit 250 francs de monnaie.",
            "sw": "Anapata chenji ya faranga 250.", "wo": "Weccit li mooy 250 franc.",
        },
        wo_review=["'weccit' for change/coins", "'marsandiis' loanword vs a Wolof term"],
    ),
    dict(
        id="eggs-04", domain="arithmetic", answer_type="numeric", gold="72",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A farmer has 6 hens. Each lays 4 eggs per week. How many eggs in 3 weeks?",
            "fr": "Un fermier a 6 poules. Chacune pond 4 œufs par semaine. Combien d'œufs en 3 semaines ?",
            "sw": "Mkulima ana kuku 6. Kila mmoja anataga mayai 4 kwa wiki. Ni mayai mangapi kwa wiki 3?",
            "wo": "Beykat bi am na 6 ginaar. Ku nekk day nqar 4 nen ci ayubés bu nekk. Ñaata nen ci 3 ayubés?",
        },
        thinking={
            "en": "In one week the hens lay 6 x 4 = 24 eggs. Over 3 weeks that is 24 x 3 = 72 eggs.",
            "fr": "En une semaine, les poules pondent 6 x 4 = 24 œufs. Sur 3 semaines cela fait 24 x 3 = 72 œufs.",
            "sw": "Kwa wiki moja kuku wanataga 6 x 4 = 24 mayai. Kwa wiki 3 ni 24 x 3 = 72 mayai.",
            "wo": "Ci benn ayubés ginaar yi dañuy nqar 6 x 4 = 24 nen. Ci 3 ayubés mooy 24 x 3 = 72 nen.",
        },
        answer={
            "en": "72 eggs.", "fr": "72 œufs.",
            "sw": "Mayai 72.", "wo": "72 nen.",
        },
        wo_review=["'nqar' for 'lay (an egg)' -- likely wrong, needs the correct verb", "'ayubés' for week"],
    ),
    dict(
        id="books-05", domain="arithmetic", answer_type="numeric", gold="24",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A class of 28 pupils needs 3 books each. The school has 60 books. How many more are needed?",
            "fr": "Une classe de 28 élèves a besoin de 3 livres chacun. L'école a 60 livres. Combien en manque-t-il ?",
            "sw": "Darasa la wanafunzi 28 linahitaji vitabu 3 kila mmoja. Shule ina vitabu 60. Vinahitajika vitabu vingapi zaidi?",
            "wo": "Klaas bu am 28 ndongo soxla na 3 téere ku nekk. Ekool bi am na 60 téere. Ñaata téere a ñu soxla ci kaw?",
        },
        thinking={
            "en": "Total books needed: 28 x 3 = 84. The school already has 60, so it needs 84 - 60 = 24 more.",
            "fr": "Livres nécessaires au total : 28 x 3 = 84. L'école en a déjà 60, il en manque donc 84 - 60 = 24.",
            "sw": "Vitabu vinavyohitajika kwa jumla: 28 x 3 = 84. Shule tayari ina 60, kwa hivyo inahitaji 84 - 60 = 24 zaidi.",
            "wo": "Téere yi ñu soxla lépp: 28 x 3 = 84. Ekool bi am na ba tey 60, kon dafa soxla 84 - 60 = 24 yu yokk.",
        },
        answer={
            "en": "24 more books are needed.", "fr": "Il manque 24 livres.",
            "sw": "Vinahitajika vitabu 24 zaidi.", "wo": "24 téere a ñu soxla ci kaw.",
        },
        wo_review=["'ci kaw' vs 'yu yokk' for 'more/additional'", "'soxla' construction with a number"],
    ),
    dict(
        id="temp-06", domain="arithmetic", answer_type="numeric", gold="25",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "At noon the temperature is 34 degrees. By evening it has dropped by 9 degrees. What is the evening temperature?",
            "fr": "À midi la température est de 34 degrés. Le soir, elle a baissé de 9 degrés. Quelle est la température du soir ?",
            "sw": "Saa sita mchana joto ni digrii 34. Ifikapo jioni limepungua kwa digrii 9. Joto la jioni ni digrii ngapi?",
            "wo": "Ci digg-bëccëg tàngoor bi mooy 34 degre. Ba ci ngoon wàcc na 9 degre. Ñaata degre la tàngoor bi ci ngoon?",
        },
        thinking={
            "en": "The temperature starts at 34 and falls by 9, so the evening value is 34 - 9 = 25 degrees.",
            "fr": "La température part de 34 et baisse de 9, donc le soir elle est de 34 - 9 = 25 degrés.",
            "sw": "Joto linaanza kwa 34 na linapungua kwa 9, kwa hivyo jioni ni 34 - 9 = 25 digrii.",
            "wo": "Tàngoor bi dafa tàmbali ci 34 te wàcc 9, kon ci ngoon mooy 34 - 9 = 25 degre.",
        },
        answer={
            "en": "25 degrees.", "fr": "25 degrés.",
            "sw": "Digrii 25.", "wo": "25 degre.",
        },
        wo_review=["'tàngoor' for temperature", "'digg-bëccëg' for noon"],
    ),
    dict(
        id="cloth-07", domain="division", answer_type="numeric", gold="4",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A tailor has 12 metres of cloth. Each dress needs 2.5 metres. How many complete dresses can he make?",
            "fr": "Un tailleur a 12 mètres de tissu. Chaque robe nécessite 2,5 mètres. Combien de robes complètes peut-il faire ?",
            "sw": "Fundi ana mita 12 za kitambaa. Kila gauni linahitaji mita 2.5. Anaweza kushona magauni mangapi kamili?",
            "wo": "Ñawkat bi am na 12 metar sér. Rob bu nekk soxla na 2.5 metar. Ñaata rob yu mat la mën a defar?",
        },
        thinking={
            "en": "Divide the cloth by the amount per dress: 12 / 2.5 = 4.8. Only complete dresses count, so he can make 4, using 10 metres and leaving 2 metres over.",
            "fr": "Je divise le tissu par la quantité par robe : 12 / 2,5 = 4,8. Seules les robes complètes comptent, il peut donc en faire 4, en utilisant 10 mètres et en laissant 2 mètres.",
            "sw": "Nagawanya kitambaa kwa kiasi cha kila gauni: 12 / 2.5 = 4.8. Magauni kamili tu yanahesabiwa, kwa hivyo anaweza kushona 4, akitumia mita 10 na kubakiza mita 2.",
            "wo": "Damay séddale sér bi ak li rob bu nekk soxla: 12 / 2.5 = 4.8. Rob yu mat rekk lañuy waññ, kon mën na defar 4, jëfandikoo 10 metar te bàyyi 2 metar.",
        },
        answer={
            "en": "He can make 4 complete dresses.", "fr": "Il peut faire 4 robes complètes.",
            "sw": "Anaweza kushona magauni 4 kamili.", "wo": "Mën na defar 4 rob yu mat.",
        },
        wo_review=["decimal 2.5 read aloud in Wolof -- comma or point, and is it read in French?",
                   "'ñawkat' for tailor", "'waññ' for count"],
    ),
    dict(
        id="savings-08", domain="arithmetic", answer_type="numeric", gold="4000",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Mariama saves 500 francs every week for 8 weeks. How much has she saved?",
            "fr": "Mariama économise 500 francs chaque semaine pendant 8 semaines. Combien a-t-elle économisé ?",
            "sw": "Mariama anaweka akiba ya faranga 500 kila wiki kwa wiki 8. Ameweka akiba ya faranga ngapi?",
            "wo": "Mariama dafay denc 500 franc ayubés bu nekk diirub 8 ayubés. Ñaata la denc?",
        },
        thinking={
            "en": "She saves the same amount each week, so the total is 500 x 8 = 4000 francs.",
            "fr": "Elle économise le même montant chaque semaine, donc le total est 500 x 8 = 4000 francs.",
            "sw": "Anaweka kiasi kilekile kila wiki, kwa hivyo jumla ni 500 x 8 = 4000 faranga.",
            "wo": "Dafay denc xaalis bu yam ayubés bu nekk, kon lépp mooy 500 x 8 = 4000 franc.",
        },
        answer={
            "en": "She has saved 4000 francs.", "fr": "Elle a économisé 4000 francs.",
            "sw": "Ameweka akiba ya faranga 4000.", "wo": "Denc na 4000 franc.",
        },
        wo_review=["'denc' for save money", "'diirub' for 'for a duration of'"],
    ),
    dict(
        id="journey-09", domain="arithmetic", answer_type="numeric", gold="83",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A driver travels 45 km, rests, then travels 38 km more. What is the total distance?",
            "fr": "Un chauffeur parcourt 45 km, se repose, puis parcourt encore 38 km. Quelle est la distance totale ?",
            "sw": "Dereva anasafiri kilomita 45, anapumzika, kisha anasafiri kilomita 38 zaidi. Umbali wote ni kilomita ngapi?",
            "wo": "Sofër bi dox na 45 kilomet, noppalu, ba noppi dox 38 kilomet yu yokk. Ñaata kilomet la lépp?",
        },
        thinking={
            "en": "The two legs add together: 45 + 38 = 83 km. The rest does not change the distance.",
            "fr": "Les deux étapes s'additionnent : 45 + 38 = 83 km. La pause ne change pas la distance.",
            "sw": "Safari mbili zinajumlishwa: 45 + 38 = 83 kilomita. Kupumzika hakubadilishi umbali.",
            "wo": "Ñaari yoon yi dañuy boole: 45 + 38 = 83 kilomet. Noppalu du soppi yoon wi.",
        },
        answer={
            "en": "The total distance is 83 km.", "fr": "La distance totale est de 83 km.",
            "sw": "Umbali wote ni kilomita 83.", "wo": "Lépp mooy 83 kilomet.",
        },
        wo_review=["'noppalu' for rest", "'boole' for add together"],
    ),
    dict(
        id="discount-10", domain="percentage", answer_type="numeric", gold="3000",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A radio costs 4000 francs. There is a 25% discount. What is the new price?",
            "fr": "Une radio coûte 4000 francs. Il y a une remise de 25 %. Quel est le nouveau prix ?",
            "sw": "Redio ina gharama ya faranga 4000. Kuna punguzo la asilimia 25. Bei mpya ni faranga ngapi?",
            "wo": "Rajo bi jar na 4000 franc. Am na wàññi bu tollu ci 25%. Ñaata la njëg bu bees bi?",
        },
        thinking={
            "en": "25% of 4000 is 4000 x 25 / 100 = 1000. Subtracting the discount: 4000 - 1000 = 3000 francs.",
            "fr": "25 % de 4000 font 4000 x 25 / 100 = 1000. En soustrayant la remise : 4000 - 1000 = 3000 francs.",
            "sw": "Asilimia 25 ya 4000 ni 4000 x 25 / 100 = 1000. Nikiondoa punguzo: 4000 - 1000 = 3000 faranga.",
            "wo": "25% ci 4000 mooy 4000 x 25 / 100 = 1000. Bu ma bàyyee wàññi bi: 4000 - 1000 = 3000 franc.",
        },
        answer={
            "en": "The new price is 3000 francs.", "fr": "Le nouveau prix est de 3000 francs.",
            "sw": "Bei mpya ni faranga 3000.", "wo": "Njëg bu bees bi mooy 3000 franc.",
        },
        wo_review=["'wàññi' for discount/reduction", "how percentages are normally spoken in Wolof"],
    ),
]

SAMPLES += [
    dict(
        id="bottles-11", domain="arithmetic", answer_type="numeric", gold="168",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "There are 7 boxes of soda, each holding 24 bottles. How many bottles in total?",
            "fr": "Il y a 7 caisses de soda, chacune contenant 24 bouteilles. Combien de bouteilles au total ?",
            "sw": "Kuna masanduku 7 ya soda, kila moja lina chupa 24. Kuna chupa ngapi kwa jumla?",
            "wo": "Am na 7 kees sooda, ku nekk am 24 buteel. Ñaata buteel a am lépp?",
        },
        thinking={
            "en": "Each box has the same number of bottles, so I multiply: 7 x 24 = 168 bottles.",
            "fr": "Chaque caisse contient le même nombre de bouteilles, donc je multiplie : 7 x 24 = 168 bouteilles.",
            "sw": "Kila sanduku lina idadi ileile ya chupa, kwa hivyo nazidisha: 7 x 24 = 168 chupa.",
            "wo": "Kees bu nekk am na limu buteel bu yam, kon damay wutal: 7 x 24 = 168 buteel.",
        },
        answer={
            "en": "168 bottles.", "fr": "168 bouteilles.",
            "sw": "Chupa 168.", "wo": "168 buteel.",
        },
        wo_review=["'wutal' for multiply -- is there a settled arithmetic verb?", "'kees' for box/crate"],
    ),
    dict(
        id="seedlings-12", domain="arithmetic", answer_type="numeric", gold="49",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A garden has 6 rows of 9 seedlings. 5 seedlings died. How many are left?",
            "fr": "Un jardin a 6 rangées de 9 plants. 5 plants sont morts. Combien en reste-t-il ?",
            "sw": "Bustani ina safu 6 za miche, kila safu ina miche 9. Miche 5 imekufa. Imebaki miche mingapi?",
            "wo": "Tool bi am na 6 rëdd yu am 9 garab yu ndaw. 5 ci ñoom dee nañu. Ñaata a des?",
        },
        thinking={
            "en": "Total planted: 6 x 9 = 54 seedlings. Then 5 died, so 54 - 5 = 49 remain.",
            "fr": "Total planté : 6 x 9 = 54 plants. Ensuite 5 sont morts, donc 54 - 5 = 49 restent.",
            "sw": "Jumla iliyopandwa: 6 x 9 = 54 miche. Kisha miche 5 imekufa, kwa hivyo 54 - 5 = 49 imebaki.",
            "wo": "Li ñu ji lépp: 6 x 9 = 54 garab. Ba noppi 5 dee nañu, kon 54 - 5 = 49 a des.",
        },
        answer={
            "en": "49 seedlings are left.", "fr": "Il reste 49 plants.",
            "sw": "Imebaki miche 49.", "wo": "49 a des.",
        },
        wo_review=["'garab yu ndaw' for seedling -- likely a better single term exists", "'ji' for plant (verb)"],
    ),
    dict(
        id="workday-13", domain="time", answer_type="numeric", gold="465",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Aissatou works from 08:00 to 16:30 with a 45-minute break. How many minutes does she actually work?",
            "fr": "Aissatou travaille de 08:00 à 16:30 avec une pause de 45 minutes. Combien de minutes travaille-t-elle réellement ?",
            "sw": "Aissatou anafanya kazi kutoka 08:00 hadi 16:30 akiwa na mapumziko ya dakika 45. Anafanya kazi dakika ngapi hasa?",
            "wo": "Aissatou dafay liggéey la ko dale ci 08:00 ba 16:30, am 45 simili noppalu. Ñaata simili la liggéey dëgg-dëgg?",
        },
        thinking={
            "en": "From 08:00 to 16:30 is 8 hours 30 minutes, which is 8 x 60 + 30 = 510 minutes. Removing the break: 510 - 45 = 465 minutes.",
            "fr": "De 08:00 à 16:30 il y a 8 heures 30, soit 8 x 60 + 30 = 510 minutes. En retirant la pause : 510 - 45 = 465 minutes.",
            "sw": "Kutoka 08:00 hadi 16:30 ni masaa 8 na dakika 30, yaani 8 x 60 + 30 = 510 dakika. Nikiondoa mapumziko: 510 - 45 = 465 dakika.",
            "wo": "La ko dale ci 08:00 ba 16:30 mooy 8 waxtu ak 30 simili, maanaam 8 x 60 + 30 = 510 simili. Bu ma bàyyee noppalu bi: 510 - 45 = 465 simili.",
        },
        answer={
            "en": "She works 465 minutes.", "fr": "Elle travaille 465 minutes.",
            "sw": "Anafanya kazi dakika 465.", "wo": "Dafay liggéey 465 simili.",
        },
        wo_review=["'simili' for minute vs the French 'minute'", "'waxtu' for hour", "'dëgg-dëgg' for 'actually'"],
    ),
    dict(
        id="fish-14", domain="arithmetic", answer_type="numeric", gold="3600",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Fish costs 1200 francs per kilogram. How much do 3 kilograms cost?",
            "fr": "Le poisson coûte 1200 francs le kilogramme. Combien coûtent 3 kilogrammes ?",
            "sw": "Samaki wanauzwa faranga 1200 kwa kilo. Kilo 3 zina gharama ya faranga ngapi?",
            "wo": "Jën jar na 1200 franc ci kilo bu nekk. Ñaata la 3 kilo jar?",
        },
        thinking={
            "en": "The price is per kilogram, so I multiply by the weight: 1200 x 3 = 3600 francs.",
            "fr": "Le prix est au kilogramme, donc je multiplie par le poids : 1200 x 3 = 3600 francs.",
            "sw": "Bei ni kwa kilo, kwa hivyo nazidisha kwa uzito: 1200 x 3 = 3600 faranga.",
            "wo": "Njëg li ci kilo la, kon damay wutal ak diis bi: 1200 x 3 = 3600 franc.",
        },
        answer={
            "en": "3600 francs.", "fr": "3600 francs.",
            "sw": "Faranga 3600.", "wo": "3600 franc.",
        },
        wo_review=["'jën' for fish", "'diis' for weight"],
    ),
    dict(
        id="fees-15", domain="arithmetic", answer_type="numeric", gold="5500",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "School fees are 15000 francs. A family has paid 9500 francs. How much is still owed?",
            "fr": "Les frais de scolarité sont de 15000 francs. Une famille a payé 9500 francs. Combien reste-t-il à payer ?",
            "sw": "Ada ya shule ni faranga 15000. Familia imelipa faranga 9500. Zimebaki faranga ngapi za kulipa?",
            "wo": "Njëgu ekool bi mooy 15000 franc. Njaboot gi fey na 9500 franc. Ñaata la des ci fey?",
        },
        thinking={
            "en": "Subtract what has been paid from the total: 15000 - 9500 = 5500 francs still owed.",
            "fr": "Je soustrais ce qui a été payé du total : 15000 - 9500 = 5500 francs restent à payer.",
            "sw": "Naondoa kilicholipwa kutoka jumla: 15000 - 9500 = 5500 faranga zimebaki.",
            "wo": "Damay bàyyi li ñu fey ci lépp: 15000 - 9500 = 5500 franc a des.",
        },
        answer={
            "en": "5500 francs are still owed.", "fr": "Il reste 5500 francs à payer.",
            "sw": "Zimebaki faranga 5500.", "wo": "5500 franc a des ci fey.",
        },
        wo_review=["'njaboot' for family", "'des ci fey' for 'remains to be paid'"],
    ),
    dict(
        id="schedule-16", domain="logic", answer_type="exact", gold="Khady",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Khady works on Monday and Wednesday. Ibrahima works on Tuesday and Thursday. Who works on Wednesday?",
            "fr": "Khady travaille le lundi et le mercredi. Ibrahima travaille le mardi et le jeudi. Qui travaille le mercredi ?",
            "sw": "Khady anafanya kazi Jumatatu na Jumatano. Ibrahima anafanya kazi Jumanne na Alhamisi. Ni nani anayefanya kazi Jumatano?",
            "wo": "Khady dafay liggéey Altine ak Àllarba. Ibrahima dafay liggéey Talaata ak Alxames. Kan mooy liggéey Àllarba?",
        },
        thinking={
            "en": "Khady's days are Monday and Wednesday. Ibrahima's days are Tuesday and Thursday. Wednesday appears only in Khady's list, so the answer is Khady.",
            "fr": "Les jours de Khady sont lundi et mercredi. Ceux d'Ibrahima sont mardi et jeudi. Mercredi n'apparaît que chez Khady, donc la réponse est Khady.",
            "sw": "Siku za Khady ni Jumatatu na Jumatano. Siku za Ibrahima ni Jumanne na Alhamisi. Jumatano inapatikana kwa Khady pekee, kwa hivyo jibu ni Khady.",
            "wo": "Bés yu Khady mooy Altine ak Àllarba. Yu Ibrahima mooy Talaata ak Alxames. Àllarba nekk na rekk ci bés yu Khady, kon tontu li mooy Khady.",
        },
        answer={
            "en": "Khady", "fr": "Khady", "sw": "Khady", "wo": "Khady",
        },
        wo_review=["day names Altine/Talaata/Àllarba/Alxames spelling"],
    ),
    dict(
        id="unitprice-17", domain="comparison", answer_type="numeric", gold="400",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "A 2-litre bottle costs 900 francs. A 3-litre bottle costs 1200 francs. What is the price per litre of the cheaper option?",
            "fr": "Une bouteille de 2 litres coûte 900 francs. Une bouteille de 3 litres coûte 1200 francs. Quel est le prix au litre de l'option la moins chère ?",
            "sw": "Chupa ya lita 2 inauzwa faranga 900. Chupa ya lita 3 inauzwa faranga 1200. Bei ya lita moja kwa chupa iliyo nafuu zaidi ni faranga ngapi?",
            "wo": "Buteel bu 2 liitar jar na 900 franc. Buteel bu 3 liitar jar na 1200 franc. Ñaata la liitar bi jar ci bi gëna yomb?",
        },
        thinking={
            "en": "Price per litre for the first: 900 / 2 = 450. For the second: 1200 / 3 = 400. 400 is less than 450, so the 3-litre bottle is cheaper per litre, at 400 francs.",
            "fr": "Prix au litre pour la première : 900 / 2 = 450. Pour la seconde : 1200 / 3 = 400. 400 est inférieur à 450, donc la bouteille de 3 litres est moins chère, à 400 francs le litre.",
            "sw": "Bei ya lita moja kwa ya kwanza: 900 / 2 = 450. Kwa ya pili: 1200 / 3 = 400. 400 ni chini ya 450, kwa hivyo chupa ya lita 3 ni nafuu zaidi, kwa faranga 400 kwa lita.",
            "wo": "Njëgu liitar ci bu njëkk bi: 900 / 2 = 450. Ci ñaareel bi: 1200 / 3 = 400. 400 dafa gëna tuuti 450, kon buteel bu 3 liitar bi mooy gëna yomb, ci 400 franc liitar bi.",
        },
        answer={
            "en": "400 francs per litre.", "fr": "400 francs le litre.",
            "sw": "Faranga 400 kwa lita.", "wo": "400 franc liitar bi.",
        },
        wo_review=["'yomb' for cheap", "'ñaareel' for second (ordinal)", "'gëna tuuti' for 'less than'"],
    ),
    dict(
        id="calendar-18", domain="time", answer_type="numeric", gold="24",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "How many days are there from 10 May to 3 June?",
            "fr": "Combien de jours y a-t-il du 10 mai au 3 juin ?",
            "sw": "Kuna siku ngapi kutoka tarehe 10 Mei hadi tarehe 3 Juni?",
            "wo": "Ñaata fan a am la ko dale ci 10 Me ba 3 Suwe?",
        },
        thinking={
            "en": "May has 31 days, so from 10 May to 31 May is 31 - 10 = 21 days. Then add the 3 days of June: 21 + 3 = 24 days.",
            "fr": "Mai a 31 jours, donc du 10 mai au 31 mai il y a 31 - 10 = 21 jours. J'ajoute ensuite les 3 jours de juin : 21 + 3 = 24 jours.",
            "sw": "Mei ina siku 31, kwa hivyo kutoka tarehe 10 Mei hadi 31 Mei ni 31 - 10 = 21 siku. Kisha naongeza siku 3 za Juni: 21 + 3 = 24 siku.",
            "wo": "Me am na 31 fan, kon la ko dale ci 10 Me ba 31 Me mooy 31 - 10 = 21 fan. Ba noppi ma yokk 3 fan yu Suwe: 21 + 3 = 24 fan.",
        },
        answer={
            "en": "24 days.", "fr": "24 jours.",
            "sw": "Siku 24.", "wo": "24 fan.",
        },
        wo_review=["month names Me / Suwe -- French borrowings, confirm the usual written forms",
                   "'fan' for day vs 'bés'"],
    ),
    dict(
        id="weights-19", domain="arithmetic", answer_type="numeric", gold="31",
        system="Think step by step, then state the final answer on its own line.",
        question={
            "en": "Three bags weigh 5 kg each and two bags weigh 8 kg each. What is the total weight?",
            "fr": "Trois sacs pèsent 5 kg chacun et deux sacs pèsent 8 kg chacun. Quel est le poids total ?",
            "sw": "Mifuko mitatu ina uzito wa kilo 5 kila mmoja na mifuko miwili ina kilo 8 kila mmoja. Uzito wote ni kilo ngapi?",
            "wo": "Ñett mboot ku nekk diis na 5 kilo te ñaar mboot ku nekk diis na 8 kilo. Ñaata kilo la lépp diis?",
        },
        thinking={
            "en": "The light bags weigh 3 x 5 = 15 kg. The heavy bags weigh 2 x 8 = 16 kg. Together that is 15 + 16 = 31 kg.",
            "fr": "Les sacs légers pèsent 3 x 5 = 15 kg. Les sacs lourds pèsent 2 x 8 = 16 kg. Ensemble cela fait 15 + 16 = 31 kg.",
            "sw": "Mifuko myepesi ina uzito wa 3 x 5 = 15 kilo. Mifuko mizito ina 2 x 8 = 16 kilo. Kwa pamoja ni 15 + 16 = 31 kilo.",
            "wo": "Mboot yu woyof yi diis nañu 3 x 5 = 15 kilo. Mboot yu diis yi diis nañu 2 x 8 = 16 kilo. Boole ko mooy 15 + 16 = 31 kilo.",
        },
        answer={
            "en": "The total weight is 31 kg.", "fr": "Le poids total est de 31 kg.",
            "sw": "Uzito wote ni kilo 31.", "wo": "Lépp diis na 31 kilo.",
        },
        wo_review=["'woyof' for light (weight)", "using 'diis' as both noun and verb"],
    ),
    dict(
        id="instruct-20", domain="instruction-following", answer_type="numeric", gold="42",
        system="Reason step by step. Your final answer must be the number alone, with no words.",
        question={
            "en": "What is 17 + 25?",
            "fr": "Combien font 17 + 25 ?",
            "sw": "17 + 25 ni ngapi?",
            "wo": "Ñaata la 17 + 25?",
        },
        thinking={
            "en": "I add the units: 7 + 5 = 12, so I write 2 and carry 1. Then the tens: 1 + 2 + 1 = 4. That gives 42. The instruction says the answer must be the number alone.",
            "fr": "J'additionne les unités : 7 + 5 = 12, j'écris 2 et je retiens 1. Puis les dizaines : 1 + 2 + 1 = 4. Cela donne 42. La consigne dit que la réponse doit être le nombre seul.",
            "sw": "Najumlisha mamoja: 7 + 5 = 12, naandika 2 na nabeba 1. Kisha makumi: 1 + 2 + 1 = 4. Hiyo inatoa 42. Maelekezo yanasema jibu liwe nambari pekee.",
            "wo": "Damay boole yu ndaw yi: 7 + 5 = 12, ma bind 2 te yóbbu 1. Ba noppi fukk yi: 1 + 2 + 1 = 4. Loolu mooy joxe 42. Ndigal li nee na tontu li war na doon limu bi rekk.",
        },
        answer={"en": "42", "fr": "42", "sw": "42", "wo": "42"},
        wo_review=["'yóbbu' for 'carry' in addition", "'ndigal' for instruction",
                   "whether carrying is normally described in Wolof at all, or done in French"],
    ),
]
