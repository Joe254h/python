"""Dependency-free text analytics: tokenising, sentiment, keyword density.

Deliberately lexicon-based rather than model-based so the tool runs offline,
fast, and with no GPU. Lexicons cover English plus common Kenyan-Swahili
campaign vocabulary, since that is where the tool is most often pointed.
"""

from __future__ import annotations

import math
import re
from collections import Counter

WORD_RE = re.compile(r"[a-zA-ZÀ-ɏ']{2,}")

STOP = {
    "the", "and", "for", "that", "this", "with", "from", "have", "has", "had", "was", "were",
    "are", "is", "be", "been", "being", "will", "would", "shall", "should", "can", "could",
    "may", "might", "must", "not", "but", "you", "your", "our", "their", "his", "her", "its",
    "they", "them", "we", "he", "she", "it", "as", "at", "by", "of", "on", "in", "to", "an",
    "a", "or", "if", "so", "than", "then", "there", "here", "who", "what", "when", "where",
    "how", "why", "all", "any", "some", "more", "most", "other", "into", "over", "after",
    "before", "just", "now", "also", "very", "about", "out", "up", "down", "one", "two",
    "said", "says", "say", "new", "via", "amp", "http", "https", "www", "com", "co", "rt",
    "na", "ya", "wa", "kwa", "ni", "hii", "hiyo", "sana", "tu", "pia", "lakini", "kama",
}

POSITIVE = {
    "good", "great", "excellent", "best", "strong", "win", "winning", "won", "support",
    "supported", "supporting", "hope", "hopeful", "trust", "trusted", "credible", "honest",
    "integrity", "development", "progress", "improve", "improved", "better", "praise",
    "praised", "champion", "leader", "leadership", "vision", "visionary", "inspiring",
    "impressive", "popular", "loved", "respect", "respected", "delivers", "delivered",
    "transparent", "accountable", "grassroots", "unifying", "peaceful", "solution",
    "opportunity", "empower", "empowering", "growth", "success", "successful", "endorse",
    "endorsed", "endorsement", "welcome", "welcomed", "thank", "thanks", "congratulations",
    "mzuri", "poa", "safi", "maendeleo", "amani", "umoja", "tunaunga", "tumeunga",
}

NEGATIVE = {
    "bad", "worst", "weak", "lose", "losing", "lost", "corrupt", "corruption", "scandal",
    "fraud", "stole", "theft", "loot", "looting", "fail", "failed", "failure", "empty",
    "lies", "lie", "liar", "dishonest", "betray", "betrayed", "tribalism", "hate", "hatred",
    "violence", "violent", "chaos", "riot", "arrest", "arrested", "court", "charged",
    "criticised", "criticized", "criticism", "attack", "attacked", "protest", "angry",
    "anger", "disappointed", "disappointing", "poor", "useless", "absent", "missing",
    "unpopular", "reject", "rejected", "rejection", "boo", "booed", "heckled", "impeach",
    "wizi", "ufisadi", "uongo", "vurugu", "hasira", "mbaya",
}

NEGATORS = {"not", "no", "never", "hardly", "barely", "without", "cannot", "cant", "isnt", "dont"}
INTENSIFIERS = {"very", "extremely", "hugely", "massively", "totally", "so", "really", "highly"}

# Vocabulary families used by the metric scorers.
KEYWORD_SETS: dict[str, set[str]] = {
    # concrete policy / manifesto language
    "policy": {
        "manifesto", "policy", "policies", "plan", "plans", "pledge", "pledges", "promise",
        "agenda", "blueprint", "roadmap", "budget", "bursary", "bursaries", "healthcare",
        "hospital", "dispensary", "education", "school", "schools", "classroom", "water",
        "borehole", "roads", "road", "electricity", "jobs", "employment", "youth", "women",
        "farmers", "agriculture", "dairy", "market", "markets", "sme", "trade", "housing",
        "security", "devolution", "county", "ward", "bill", "act", "reform", "reforms",
        "fund", "funding", "cdf", "ngaaf", "sacco", "irrigation", "fertiliser", "fertilizer",
    },
    # commitments with numbers / deadlines - a clarity signal
    "commitment": {
        "will", "shall", "commit", "committed", "commitment", "deliver", "deliverables",
        "within", "first", "days", "years", "target", "targets", "by", "ensure", "increase",
        "build", "construct", "establish", "create", "reduce", "double", "triple",
    },
    # physical, offline activity - the ground-visibility signal
    "ground": {
        "rally", "rallies", "roadshow", "roadshows", "tour", "toured", "visit", "visited",
        "meeting", "meetings", "baraza", "mabaraza", "harambee", "fundraiser", "church",
        "mosque", "funeral", "burial", "wedding", "market", "village", "ward", "location",
        "sublocation", "constituency", "grassroots", "door", "doorstep", "walk", "walked",
        "crowd", "crowds", "turnout", "residents", "voters", "delegates", "mobilise",
        "mobilize", "mobilisation", "mobilization", "campaign", "campaigning", "launch",
        "launched", "ground", "field", "chief", "elders", "boda", "matatu", "stage",
        "sokoni", "mkutano", "wananchi", "mtaa", "kijiji",
    },
    # organic momentum words
    "momentum": {
        "surge", "surging", "rising", "rise", "gaining", "gains", "wave", "trending",
        "trend", "sweep", "sweeping", "unstoppable", "frontrunner", "favourite", "favorite",
        "lead", "leading", "shift", "swing", "defect", "defected", "defection", "joined",
        "joining", "endorsed", "endorsement", "declared", "declare",
    },
}

NUMBER_RE = re.compile(r"\b\d[\d,.]*\b")


def tokenize(text: str, drop_stopwords: bool = True) -> list[str]:
    words = [w.lower() for w in WORD_RE.findall(text or "")]
    if drop_stopwords:
        words = [w for w in words if w not in STOP]
    return words


def top_terms(texts: list[str], n: int = 15) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for t in texts:
        counter.update(set(tokenize(t)))  # set() => document frequency, not raw frequency
    return counter.most_common(n)


def sentiment_score(text: str) -> float:
    """Return a sentiment value in [-1, 1]. 0 when no polar words are present."""
    words = tokenize(text, drop_stopwords=False)
    if not words:
        return 0.0
    score = 0.0
    hits = 0
    for i, word in enumerate(words):
        polarity = 1.0 if word in POSITIVE else (-1.0 if word in NEGATIVE else 0.0)
        if polarity == 0.0:
            continue
        window = words[max(0, i - 3): i]
        if any(w in NEGATORS for w in window):
            polarity *= -0.8
        if any(w in INTENSIFIERS for w in window):
            polarity *= 1.4
        score += polarity
        hits += 1
    if not hits:
        return 0.0
    return max(-1.0, min(1.0, score / (hits ** 0.5) / 2.0))


def keyword_density(text: str, family: str) -> float:
    """Share of tokens belonging to a keyword family, in [0, 1]."""
    vocab = KEYWORD_SETS.get(family, set())
    words = tokenize(text, drop_stopwords=False)
    if not words:
        return 0.0
    return sum(1 for w in words if w in vocab) / len(words)


def normalised_entropy(counter: Counter[str]) -> float:
    """Shannon entropy of a distribution, scaled to [0, 1]. 0 = single topic."""
    total = sum(counter.values())
    if total <= 0 or len(counter) <= 1:
        return 0.0
    h = -sum((c / total) * math.log(c / total, 2) for c in counter.values() if c)
    return h / math.log(len(counter), 2)


def has_numbers(text: str) -> bool:
    return bool(NUMBER_RE.search(text or ""))
