"""Closed-set language identification for Swahili, Wolof, English, French.

Why not an off-the-shelf detector: the usual choices (langdetect, langid.py,
fastText lid.176) either do not cover Wolof at all or cover it badly, and in
this environment every model host is blocked by egress policy so none of them
could be downloaded anyway. For a closed 4-way decision, weighted function
words plus orthographic cues are both sufficient and auditable -- you can read
why a call was made, which matters when the call is evidence in an evaluation.

The important output is not `top` but `mixture`. The failure this project
exists to catch is a model that reasons in English and answers in English when
asked in Wolof; the failure it must NOT mistake for that is natural Wolof
containing French numerals and loanwords, which is ordinary speech, not
collapse. Only a mixture breakdown can tell those apart.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

LANGUAGES = ("en", "fr", "sw", "wo")

# High-frequency function words. Content words are deliberately excluded: they
# are what translation changes, so they make poor evidence of language.
_MARKERS: dict[str, set[str]] = {
    "en": {
        "the", "and", "of", "to", "in", "is", "it", "that", "for", "we", "so",
        "then", "first", "if", "but", "with", "this", "have", "are", "be", "as",
        "at", "on", "by", "from", "or", "not", "can", "will", "each", "there",
        "need", "let", "now", "total", "answer", "because", "therefore",
        "since", "thus", "next", "finally", "step", "how", "many", "what",
        "which", "they", "their", "them", "was", "were", "an", "his", "her",
        "she", "he", "you", "i", "my", "me", "do", "does", "did", "should",
        "would", "could", "about", "into", "than", "more", "most", "also",
    },
    "fr": {
        "le", "la", "les", "de", "des", "du", "et", "un", "une", "est", "dans",
        "que", "qui", "pour", "sur", "avec", "il", "elle", "nous", "vous",
        "ne", "pas", "plus", "donc", "alors", "ensuite", "enfin", "ainsi",
        "car", "mais", "ou", "au", "aux", "ce", "cette", "se", "sont", "ont",
        "par", "en", "son", "sa", "leur", "chaque", "réponse", "reponse",
        "calcul", "puis", "abord", "combien", "sur", "aussi", "tout", "tous",
        "toute", "toutes", "être", "etre", "avoir", "fait", "faire", "peut",
        "doit", "je", "tu", "on", "y", "ses", "mes", "nos", "vos", "quel",
        "quelle", "comme", "même", "meme", "très", "tres", "bien", "encore",
    },
    "sw": {
        "na", "ya", "wa", "ni", "kwa", "katika", "la", "za", "cha", "vya",
        "hiyo", "hii", "huyo", "kuwa", "kama", "lakini", "basi", "kisha",
        "kwanza", "hivyo", "sasa", "jumla", "jibu", "hesabu", "kila", "ana",
        "yake", "yangu", "wake", "zao", "ambayo", "ambao", "kwenye", "pia",
        "tu", "si", "bado", "ili", "nini", "je", "ndiyo", "hapo", "hapa",
        "yule", "wale", "hao", "zile", "vile", "ile", "lile", "mimi", "wewe",
        "yeye", "sisi", "nyinyi", "wao", "tuna", "nina", "ana", "wana",
        "tunahitaji", "ninahitaji", "anahitaji", "kuhesabu", "kupata",
        "sasa", "halafu", "mwisho", "kwahiyo", "ngapi", "nyingi", "wote",
        "zote", "yote", "chake", "lake", "baada", "kabla", "juu", "chini",
    },
    "wo": {
        "ak", "ci", "ba", "bu", "bi", "mi", "gi", "nga", "naa", "dafa",
        "dama", "danga", "mu", "ñu", "ngi", "lu", "ku", "kii", "boobu",
        "waaye", "kon", "ndax", "ndaxte", "ne", "def", "am", "amul", "benn",
        "ñaar", "ñett", "ñeent", "juróom", "juroom", "fukk", "moom", "moo",
        "yow", "man", "lépp", "lepp", "yépp", "yepp", "bépp", "bepp", "li",
        "yi", "gu", "wu", "su", "te", "walla", "itam", "noonu", "mooy",
        "dina", "du", "deful", "tey", "léegi", "leegi", "xam", "xalaat",
        "jënd", "jend", "yaa", "sama", "sa", "seen", "nekk", "wax", "jël",
        "jel", "boo", "bare", "ñaari", "ñetti", "teg", "gannaaw", "njëkk",
        "njekk", "mel", "lan", "ñaata", "naata", "kañ", "fan", "loolu",
    },
}

# Numerals are kept separate because they carry most of the code-switching
# signal in this project: Wolof speakers routinely count in French, so whether
# French number words appear in a Wolof trace is a measurement we need, not
# noise to suppress.
_NUMERALS: dict[str, set[str]] = {
    "en": {
        "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "twenty", "thirty", "forty",
        "fifty", "hundred", "thousand", "half", "times", "equals",
    },
    "fr": {
        "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
        "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
        "vingt", "trente", "quarante", "cinquante", "soixante", "cent",
        "cents", "mille", "demi", "moitié", "moitie", "fois", "égal", "egal",
    },
    "sw": {
        "moja", "mbili", "tatu", "nne", "tano", "sita", "saba", "nane",
        "tisa", "kumi", "ishirini", "thelathini", "arobaini", "hamsini",
        "sitini", "sabini", "themanini", "tisini", "mia", "elfu", "nusu",
        "mara", "sawa",
    },
    "wo": {
        "benn", "ñaar", "naar", "ñett", "nett", "ñeent", "neent", "juróom",
        "juroom", "fukk", "téeméer", "teemeer", "junni", "genn", "ñaari",
        "ñetti", "ñeenti", "juróomi", "digg", "yoon",
    },
}
for _lang, _nums in _NUMERALS.items():
    _MARKERS[_lang] = _MARKERS[_lang] | _nums

# A token in several lists is weak evidence. Weight it by how many lists it is
# in, so shared spellings like "na" / "ni" / "la" stop dominating the score.
_WEIGHTS: dict[str, dict[str, float]] = {}
_SHARE_COUNT: dict[str, int] = {}
for _lang, _words in _MARKERS.items():
    for _w in _words:
        _SHARE_COUNT[_w] = _SHARE_COUNT.get(_w, 0) + 1
for _lang, _words in _MARKERS.items():
    _WEIGHTS[_lang] = {_w: 1.0 / _SHARE_COUNT[_w] for _w in _words}

# Orthographic cues, applied per-character over the whole string.
_CHAR_CUES: dict[str, str] = {
    "wo": "ëñŋ",          # official Senegalese orthography
    "fr": "éèêçàùûôîœ",   # French diacritics (à and ù overlap Wolof à, kept light)
}

_TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)


@dataclass
class LangResult:
    """A language call, with the evidence that produced it."""

    top: str
    confidence: float
    scores: dict[str, float]
    mixture: dict[str, float]
    matched: int
    total_tokens: int
    notes: list[str] = field(default_factory=list)

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.25 and self.matched >= 3


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, accents preserved (they are evidence here)."""
    return [t.lower() for t in _TOKEN.findall(unicodedata.normalize("NFC", text))]


def identify(text: str) -> LangResult:
    """Identify the dominant language and report the full mixture."""
    tokens = tokenize(text)
    scores = {lang: 0.0 for lang in LANGUAGES}
    matched = 0

    for tok in tokens:
        hit = False
        for lang in LANGUAGES:
            w = _WEIGHTS[lang].get(tok)
            if w:
                scores[lang] += w
                hit = True
        if hit:
            matched += 1

    lowered = text.lower()
    for lang, cues in _CHAR_CUES.items():
        bonus = sum(lowered.count(c) for c in cues)
        # Character cues corroborate, they do not decide: cap their weight so a
        # single accented loanword cannot flip a call.
        scores[lang] += min(bonus, 6) * 0.5

    total = sum(scores.values())
    if total <= 0:
        return LangResult("unknown", 0.0, scores, {}, matched, len(tokens),
                          ["no marker tokens found; text too short or out of set"])

    mixture = {lang: scores[lang] / total for lang in LANGUAGES}
    ranked = sorted(mixture.items(), key=lambda kv: kv[1], reverse=True)
    top, top_share = ranked[0]
    runner_share = ranked[1][1] if len(ranked) > 1 else 0.0

    notes: list[str] = []
    if len(tokens) < 8:
        notes.append("short text; call is low-evidence")
    if runner_share >= 0.25:
        notes.append(f"substantial {ranked[1][0]} content ({runner_share:.0%})")

    return LangResult(
        top=top,
        confidence=top_share - runner_share,
        scores=scores,
        mixture=mixture,
        matched=matched,
        total_tokens=len(tokens),
        notes=notes,
    )


def code_switch_ratio(text: str, base: str, other: str) -> float:
    """Share of `other` relative to `base` + `other` alone.

    Used to quantify French inside Wolof without letting English or Swahili
    noise distort the figure.
    """
    res = identify(text)
    pair = res.scores.get(base, 0.0) + res.scores.get(other, 0.0)
    if pair <= 0:
        return 0.0
    return res.scores.get(other, 0.0) / pair
