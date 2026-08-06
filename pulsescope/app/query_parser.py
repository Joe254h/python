"""Turn a plain-English launch prompt into a structured :class:`Query`.

Handles prompts like::

    Rate Philip Munialo against Moses Lupao, Emmanuel Waswa and Nick Biketi
    in terms of momentum building, message clarity and manifesto, social
    media presence and ground visibility.
"""

from __future__ import annotations

import re

from .config import settings
from .models import DEFAULT_METRICS, Metric, Query

# ---------------------------------------------------------------- metrics ---

METRIC_PATTERNS: list[tuple[Metric, tuple[str, ...]]] = [
    (Metric.MOMENTUM, ("momentum", "traction", "growth", "trend", "trajectory", "surge", "buzz")),
    (
        Metric.MESSAGE_CLARITY,
        ("message clarity", "clarity", "manifest", "manifesto", "policy", "policies",
         "agenda", "messaging", "platform of ideas", "pledges", "promises"),
    ),
    (
        Metric.SOCIAL_PRESENCE,
        ("social media presence", "social presence", "online presence", "digital presence",
         "social media", "online footprint", "followers", "digital footprint"),
    ),
    (
        Metric.GROUND_VISIBILITY,
        ("ground visibility", "ground game", "grassroots", "on the ground", "field presence",
         "visibility on the ground", "rallies", "mobilisation", "mobilization"),
    ),
    (Metric.SENTIMENT, ("sentiment", "public opinion", "approval", "perception", "favourability",
                        "favorability", "likeability", "likability")),
    (Metric.REACH, ("reach", "audience size", "impressions", "eyeballs", "exposure")),
]

# Words that are never part of a person's name even when capitalised.
STOPWORDS = {
    "rate", "rank", "compare", "compares", "comparison", "analyse", "analyze", "analysis",
    "score", "scores", "evaluate", "assess", "benchmark", "measure", "study", "review",
    "against", "versus", "vs", "and", "or", "with", "for", "the", "a", "an", "of", "on",
    "in", "terms", "term", "to", "by", "about", "between", "among", "amongst", "over",
    "please", "kindly", "me", "my", "give", "show", "find", "search", "who", "which",
    "how", "what", "is", "are", "do", "does", "based", "regarding", "concerning",
    "statistics", "stats", "data", "report", "hon", "mr", "mrs", "ms", "dr", "prof",
    "eng", "sen", "mca", "mp", "governor", "senator", "candidate", "candidates",
}

#: Every metric phrase, longest first, as one alternation.
METRIC_WORDS = "|".join(
    re.escape(k) for k in sorted(
        (k for _, keys in METRIC_PATTERNS for k in keys), key=len, reverse=True
    )
)

SPLIT_METRICS = re.compile(
    r"\b(?:in\s+terms\s+of|on\s+the\s+basis\s+of|based\s+on|with\s+respect\s+to|"
    r"regarding|according\s+to|across|measured\s+by|by\s+the\s+metrics?\s+of|"
    r"in\s+the\s+areas?\s+of|looking\s+at)\b"
    # A bare "on"/"for" only starts the metric clause when a metric phrase
    # follows close behind - otherwise "Peter on Sunday" would split.
    rf"|\b(?:on|for)\b(?=[^,;]{{0,24}}?(?:{METRIC_WORDS}))",
    re.I,
)

IS_METRIC_PHRASE = re.compile(rf"\b(?:{METRIC_WORDS})\b", re.I)

SPLIT_SUBJECTS = re.compile(r"\bagainst\b|\bversus\b|\bvs\.?\b|\bcompared\s+to\b|\bwith\b", re.I)

LEAD_VERB = re.compile(
    r"^\s*(?:can\s+you\s+)?(?:please\s+)?(?:kindly\s+)?"
    r"(?:rate|rank|compare|analyse|analyze|score|evaluate|assess|benchmark|"
    r"measure|review|study|profile|research)\s+",
    re.I,
)

# A place small enough to scope a search by, but not a country code.
LOCALITY_HINT = re.compile(
    r"\bin\s+([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)?)\s+"
    r"(?:county|ward|constituency|sub-?county|district|region|city|town|province|state)\b"
)

COUNTRIES = {
    "kenya": "KE", "uganda": "UG", "tanzania": "TZ", "rwanda": "RW", "burundi": "BI",
    "ethiopia": "ET", "somalia": "SO", "south sudan": "SS", "nigeria": "NG", "ghana": "GH",
    "south africa": "ZA", "zambia": "ZM", "zimbabwe": "ZW", "malawi": "MW", "botswana": "BW",
    "united kingdom": "GB", "uk": "GB", "britain": "GB", "united states": "US", "usa": "US",
    "us": "US", "america": "US", "india": "IN", "canada": "CA", "australia": "AU",
}
COUNTRY_HINT = re.compile(
    r"\bin\s+(?:the\s+)?(" + "|".join(sorted(COUNTRIES, key=len, reverse=True)) + r")\b", re.I
)

#: Any geographic scoping clause - stripped before names are split out.
GEO_CLAUSE = re.compile(
    LOCALITY_HINT.pattern + "|" + COUNTRY_HINT.pattern, re.I
)

# Tail clauses that belong to neither the subject list nor the metric list.
TRAILING_CLAUSE = re.compile(
    r"\b(?:over|during|within|throughout|across)\s+the\s+(?:last|past|previous)\b.*$"
    r"|\b(?:since|starting)\s+\d.*$"
    r"|\band\s+(?:give|show|tell|send|get)\s+me\b.*$"
    r"|\bwith\s+(?:statistics|stats|charts?|numbers?|data)\b.*$",
    re.I,
)

LOOKBACK_HINT = re.compile(
    r"(?:last|past|previous)\s+(\d+)\s*(day|days|week|weeks|month|months|year|years)", re.I
)

PLATFORM_HINT = {
    "x": "x", "twitter": "x", "facebook": "facebook", "fb": "facebook",
    "instagram": "instagram", "ig": "instagram", "tiktok": "tiktok",
    "youtube": "youtube", "reddit": "reddit", "news": "news", "web": "web",
    "linkedin": "linkedin",
}


def _clean_name(chunk: str) -> str:
    """Normalise one candidate name fragment; return '' when it isn't a name."""
    chunk = re.sub(r"[\"'`()\[\]{}]", " ", chunk)
    chunk = re.sub(r"\s+", " ", chunk).strip(" .,;:-–—")
    if not chunk:
        return ""

    words = [w for w in chunk.split() if w]
    # Drop leading honorifics / role nouns.
    while words and words[0].lower().strip(".") in STOPWORDS:
        words.pop(0)
    while words and words[-1].lower().strip(".") in STOPWORDS:
        words.pop()
    if not words or len(words) > 5:
        return ""
    # A name needs at least one alphabetic token of length >= 2.
    if not any(len(w) >= 2 and w.replace("-", "").replace(".", "").isalpha() for w in words):
        return ""
    return " ".join(w.capitalize() if w.islower() or w.isupper() else w for w in words)


def _split_list(text: str) -> list[str]:
    """Split 'A, B, C and D' (also 'A; B & C') into fragments."""
    text = re.sub(r"\s*&\s*", ", ", text)
    text = re.sub(r"\s*\band\b\s*", ", ", text, flags=re.I)
    text = re.sub(r"[;/]", ",", text)
    return [p for p in (frag.strip() for frag in text.split(",")) if p]


def parse_metrics(text: str) -> list[Metric]:
    lowered = text.lower()
    found: list[Metric] = []
    for metric, keys in METRIC_PATTERNS:
        if metric in found:
            continue
        if any(k in lowered for k in keys):
            found.append(metric)
    return found


def parse_subjects(text: str) -> tuple[list[str], str | None]:
    """Return (subjects, focus). ``focus`` is the name the prompt centres on."""
    head = SPLIT_METRICS.split(text)[0]
    head = LEAD_VERB.sub("", head).strip()
    head = TRAILING_CLAUSE.sub("", head)
    head = GEO_CLAUSE.sub(" ", head).strip(" .,;:")

    focus: str | None = None
    parts = SPLIT_SUBJECTS.split(head, maxsplit=1)
    if len(parts) == 2 and _clean_name(parts[0]):
        focus = _clean_name(parts[0])
        rest = parts[1]
    else:
        rest = head

    names: list[str] = []
    if focus:
        names.append(focus)
    for frag in _split_list(rest):
        name = _clean_name(frag)
        if name and name.lower() not in {n.lower() for n in names}:
            names.append(name)

    # Safety net: a metric phrase that slipped through is never a subject.
    names = [n for n in names if not IS_METRIC_PHRASE.search(n)]

    if not names:
        # Fallback: pull capitalised runs out of the whole prompt.
        for run in re.findall(r"\b([A-Z][a-zA-Z'’\-]+(?:\s+[A-Za-z'’\-]+){0,3})", text):
            name = _clean_name(run)
            if name and name.lower() not in {n.lower() for n in names}:
                names.append(name)
    return names, focus


def parse(raw: str) -> Query:
    """Parse a free-text launch prompt into a Query."""
    text = " ".join((raw or "").split())

    subjects, focus = parse_subjects(text)
    metrics = parse_metrics(text) or list(DEFAULT_METRICS)

    lookback = settings.lookback_days
    if m := LOOKBACK_HINT.search(text):
        n, unit = int(m.group(1)), m.group(2).lower()
        lookback = n * {"day": 1, "week": 7, "month": 30, "year": 365}[unit.rstrip("s")]

    region = settings.region
    if m := COUNTRY_HINT.search(text):
        region = COUNTRIES[m.group(1).lower()]

    locality = ""
    if m := LOCALITY_HINT.search(text):
        locality = m.group(0).split(" ", 1)[1].strip()   # drop the leading "in"

    platforms = sorted(
        {
            slug
            for word, slug in PLATFORM_HINT.items()
            if re.search(rf"\bonly\s+(?:on\s+)?{re.escape(word)}\b", text, re.I)
        }
    )

    return Query(
        raw=raw,
        subjects=subjects,
        focus=focus,
        metrics=metrics,
        region=region,
        locality=locality,
        lookback_days=max(7, min(lookback, 730)),
        platforms=platforms,
    )
