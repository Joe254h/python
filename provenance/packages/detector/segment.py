"""Cut a document into the units the two engines actually work on.

Retrieval works on overlapping word n-grams (shingles); AI detection works on
paragraphs; the report highlights sentences. All three carry offsets into the
same string produced by `extract`.

This module also decides what *not* to score. A correctly quoted and cited
passage is not plagiarism, and a bibliography is a list of other people's
titles by definition -- scoring either one inflates the similarity number with
matches that mean nothing, which is the most common complaint about tools in
this category. Excluded regions are recorded as spans rather than deleted, so
every offset downstream still refers to the same text.
"""

from __future__ import annotations

import re

from .types import Document, Span

#: Word n-gram width for fingerprinting. Five is the usual choice: short
#: enough to survive light editing, long enough that ordinary English does not
#: collide by chance.
SHINGLE_SIZE = 5

#: Abbreviations that end in a period without ending a sentence.
_ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g",
    "i.e", "cf", "al", "fig", "eq", "no", "vol", "pp", "ed", "eds", "approx",
    "dept", "univ", "inc", "ltd", "co", "corp", "phd", "msc", "bsc",
}

_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_SENT_END_RE = re.compile(r"[.!?]+[\"')\]]*\s+")
_PARA_SPLIT_RE = re.compile(r"\n\s*\n")

#: Headings that begin a reference list. Matched on their own line.
_REF_HEADING_RE = re.compile(
    r"^[ \t]*(?:\d+[.)]?[ \t]*)?"
    r"(references|bibliography|works\s+cited|reference\s+list|"
    r"literature\s+cited|sources)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

#: A quoted run long enough to be a real quotation rather than scare quotes.
_QUOTE_RE = re.compile(r'"([^"\n]{40,})"')
_BLOCKQUOTE_RE = re.compile(r"^(?:>|\s{4,})(\S.*)$", re.MULTILINE)

_MIN_QUOTE_WORDS = 8


def words(text: str, offset: int = 0) -> list[tuple[str, Span]]:
    """Lowercased word tokens with their spans."""
    return [
        (m.group(0).lower(), Span(offset + m.start(), offset + m.end()))
        for m in _WORD_RE.finditer(text)
    ]


def sentences(text: str) -> list[Span]:
    """Split into sentence spans.

    Regex splitting with an abbreviation guard, not a trained model. It is
    wrong occasionally on citation-dense academic prose, which is tolerable
    because sentences are only a display unit here -- matches are found on
    shingles and scored on paragraphs, so a bad split changes how a highlight
    is grouped, never whether it is found.
    """
    spans: list[Span] = []
    start = 0
    for m in _SENT_END_RE.finditer(text):
        end = m.end()
        head = text[start:m.start() + 1].rstrip()
        last = head.split()[-1].rstrip(".").lower() if head.split() else ""
        if last in _ABBREV or (len(last) == 1 and last.isalpha()):
            continue
        if end - start >= 2:
            spans.append(Span(start, m.start() + 1))
        start = end
    if start < len(text):
        tail = text[start:].rstrip()
        if tail:
            spans.append(Span(start, start + len(tail)))
    return spans


def paragraphs(text: str, min_words: int = 25) -> list[Span]:
    """Paragraph spans, which are the unit the AI detector scores.

    Short paragraphs are merged forward rather than scored alone: perplexity
    estimates on a handful of tokens are noise, and reporting a confident
    machine-written score for a two-line heading is exactly the failure that
    gets a student wrongly accused.
    """
    raw: list[Span] = []
    cursor = 0
    for chunk in _PARA_SPLIT_RE.split(text):
        idx = text.find(chunk, cursor)
        if idx < 0:
            continue
        if chunk.strip():
            raw.append(Span(idx, idx + len(chunk)))
        cursor = idx + len(chunk)

    merged: list[Span] = []
    pending: Span | None = None
    for span in raw:
        pending = span if pending is None else pending.merge(span)
        if len(_WORD_RE.findall(text[pending.start:pending.end])) >= min_words:
            merged.append(pending)
            pending = None
    if pending is not None:
        if merged:
            merged[-1] = merged[-1].merge(pending)
        else:
            merged.append(pending)
    return merged


def shingles(
    text: str, size: int = SHINGLE_SIZE, exclude: list[Span] | None = None
) -> list[tuple[str, Span]]:
    """Overlapping word n-grams with the span they cover in the source text.

    The n-gram string is normalised (lowercase, single-spaced) so that
    reformatting does not defeat matching, while the span still points at the
    original characters for highlighting.
    """
    toks = words(text)
    exclude = exclude or []
    out: list[tuple[str, Span]] = []
    for i in range(len(toks) - size + 1):
        window = toks[i:i + size]
        span = Span(window[0][1].start, window[-1][1].end)
        if any(span.overlaps(ex) for ex in exclude):
            continue
        out.append((" ".join(w for w, _ in window), span))
    return out


def find_quotations(text: str) -> list[Span]:
    """Spans of quoted material long enough to count as a quotation."""
    found: list[Span] = []
    for m in _QUOTE_RE.finditer(text):
        if len(_WORD_RE.findall(m.group(1))) >= _MIN_QUOTE_WORDS:
            found.append(Span(m.start(), m.end()))
    for m in _BLOCKQUOTE_RE.finditer(text):
        if len(_WORD_RE.findall(m.group(1))) >= _MIN_QUOTE_WORDS:
            found.append(Span(m.start(), m.end()))
    return found


def find_references(text: str) -> list[Span]:
    """The reference list, if there is one: last matching heading to the end.

    Taking the *last* heading matters -- a paper that mentions "References" in
    its methods section should not have half its body excluded.
    """
    matches = list(_REF_HEADING_RE.finditer(text))
    if not matches:
        return []
    last = matches[-1]
    # A heading in the first half of a document is more likely a mention than
    # the real reference list.
    if last.start() < len(text) * 0.4:
        return []
    return [Span(last.start(), len(text))]


def mark_exclusions(
    doc: Document, exclude_quotes: bool = True, exclude_references: bool = True
) -> Document:
    """Populate `doc.excluded` in place and return the document."""
    found: list[Span] = []
    if exclude_quotes:
        found.extend(find_quotations(doc.text))
    if exclude_references:
        found.extend(find_references(doc.text))

    merged: list[Span] = []
    for span in sorted(found, key=lambda s: s.start):
        if merged and merged[-1].overlaps(span):
            merged[-1] = merged[-1].merge(span)
        else:
            merged.append(span)
    doc.excluded = merged
    return doc


def scored_word_count(doc: Document) -> int:
    """Words that count towards the similarity denominator.

    Excluding quotes from the numerator but not the denominator would quietly
    reward padding a paper with block quotes, so both use the same set.
    """
    return sum(
        1
        for _, span in words(doc.text)
        if not doc.is_excluded(span)
    )
