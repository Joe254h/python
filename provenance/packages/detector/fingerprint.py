"""Passage-level fingerprinting: winnowing plus an inverted index.

The obvious approach -- MinHash the whole document, bucket it with banded LSH,
compare documents that collide -- is the wrong primitive for this problem, and
it fails in a way worth recording so nobody reintroduces it.

MinHash estimates *global* Jaccard overlap. A thesis that copies one chapter
out of twelve has a global Jaccard around 0.05 against its source. LSH tuned to
surface that would return most of the corpus as a candidate for every query;
tuned to be useful, it never surfaces it at all. Whole-document near-duplicate
detection and passage-level reuse detection are different problems, and only
the second one is plagiarism detection.

So retrieval here is winnowing (Schleimer, Wilkerson & Aiken, SIGMOD 2003 --
the algorithm behind MOSS) over an inverted index. Hash every word 5-gram,
slide a window over the hash sequence, and keep the minimum hash in each
window. That selection has two properties this application needs:

  * Any shared passage of at least `k + w - 1` words is guaranteed to produce a
    shared fingerprint. With k=5 and w=8 that is 12 words -- shorter than any
    match worth reporting, so the guarantee is never the binding constraint.
  * Only about 2/(w+1) of fingerprints are stored, so the index is roughly a
    fifth the size of a naive one, with no loss of detection above threshold.

MinHash survives in this module, but demoted to what it is actually good at:
scoring how similar two documents are *overall*, once the inverted index has
already decided they are worth comparing.
"""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field

from .types import Match, Source, Span

_PRIME = (1 << 61) - 1
_MASK32 = (1 << 32) - 1

#: Window for winnowing. With SHINGLE_SIZE=5 this guarantees detection of any
#: shared run of 12 or more words, at roughly 22% fingerprint density.
WINNOW_WINDOW = 8

#: Permutations for the document-level MinHash score.
NUM_PERM = 128


def stable_hash(text: str) -> int:
    """Deterministic 32-bit hash of a shingle.

    Python's built-in hash() is randomised per interpreter run, so an index
    written today would not match a query tomorrow. blake2b costs a little
    speed and buys a persistable index.
    """
    return int.from_bytes(
        hashlib.blake2b(text.encode("utf-8"), digest_size=4).digest(), "big"
    )


# ------------------------------------------------------------------ winnowing


@dataclass(frozen=True)
class Fingerprint:
    """A selected shingle hash and the characters it covers."""

    hash: int
    span: Span


def winnow(
    shingle_spans: list[tuple[str, Span]], window: int = WINNOW_WINDOW
) -> list[Fingerprint]:
    """Select fingerprints by the winnowing algorithm.

    In each window of `window` consecutive shingle hashes, keep the minimum. On
    ties keep the rightmost occurrence -- this is the detail that makes the
    selection stable under insertion: the same passage in two documents selects
    the same fingerprints even when the surrounding text differs.
    """
    if not shingle_spans:
        return []

    hashes = [(stable_hash(text), span) for text, span in shingle_spans]
    if len(hashes) <= window:
        h, span = min(hashes, key=lambda pair: (pair[0], -pair[1].start))
        return [Fingerprint(h, span)]

    selected: list[Fingerprint] = []
    last_index = -1
    for start in range(len(hashes) - window + 1):
        chunk = hashes[start:start + window]
        best_offset = 0
        best_hash = chunk[0][0]
        for offset in range(1, window):
            # <= keeps the rightmost minimum on ties.
            if chunk[offset][0] <= best_hash:
                best_hash = chunk[offset][0]
                best_offset = offset
        index = start + best_offset
        if index != last_index:
            selected.append(Fingerprint(hashes[index][0], hashes[index][1]))
            last_index = index
    return selected


# ------------------------------------------------------------ inverted index


class FingerprintIndex:
    """Inverted index from fingerprint hash to the documents containing it.

    Two dictionaries are the entire state, so moving this to Redis or Postgres
    when it outgrows memory is a storage swap rather than a rewrite.
    """

    def __init__(self) -> None:
        self.postings: dict[int, list[tuple[str, Span]]] = defaultdict(list)
        self.doc_fingerprints: dict[str, list[Fingerprint]] = {}
        self.sources: dict[str, Source] = {}

    def __len__(self) -> int:
        return len(self.doc_fingerprints)

    def add(self, doc_id: str, fps: list[Fingerprint], source: Source) -> None:
        if doc_id in self.doc_fingerprints:
            self.remove(doc_id)
        self.doc_fingerprints[doc_id] = fps
        self.sources[doc_id] = source
        for fp in fps:
            self.postings[fp.hash].append((doc_id, fp.span))

    def remove(self, doc_id: str) -> None:
        fps = self.doc_fingerprints.pop(doc_id, None)
        self.sources.pop(doc_id, None)
        if not fps:
            return
        for fp in fps:
            bucket = self.postings.get(fp.hash)
            if not bucket:
                continue
            self.postings[fp.hash] = [p for p in bucket if p[0] != doc_id]
            if not self.postings[fp.hash]:
                del self.postings[fp.hash]

    def query(
        self, fps: list[Fingerprint], exclude: str | None = None, min_hits: int = 2
    ) -> dict[str, list[tuple[Span, Span]]]:
        """Documents sharing fingerprints, mapped to (query_span, source_span).

        `min_hits` drops documents sharing a single fingerprint. One shared
        5-gram is usually a common phrase; requiring two before a document is
        even considered removes most of that noise at no cost to real matches,
        which share many.
        """
        hits: dict[str, list[tuple[Span, Span]]] = defaultdict(list)
        for fp in fps:
            for doc_id, source_span in self.postings.get(fp.hash, ()):
                if doc_id == exclude:
                    continue
                hits[doc_id].append((fp.span, source_span))
        return {d: pairs for d, pairs in hits.items() if len(pairs) >= min_hits}


# ------------------------------------------------------- document-level score


def _permutations(seed: int = 20260907) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    return [
        (rng.randrange(1, _PRIME), rng.randrange(0, _PRIME)) for _ in range(NUM_PERM)
    ]


_PERMS = _permutations()


@dataclass(frozen=True)
class Signature:
    """MinHash signature, used to score a candidate pair -- not to find one."""

    values: tuple[int, ...] = field(default=())

    def jaccard(self, other: "Signature") -> float:
        if not self.values or not other.values:
            return 0.0
        agree = sum(1 for a, b in zip(self.values, other.values) if a == b)
        return agree / len(self.values)


def minhash(shingle_spans: list[tuple[str, Span]]) -> Signature:
    """Whole-document signature. Empty input yields an all-max signature
    rather than an exception -- a two-word submission is a real upload and
    should score zero, not crash a worker."""
    if not shingle_spans:
        return Signature(values=tuple([_MASK32] * NUM_PERM))

    unique = {stable_hash(text) for text, _ in shingle_spans}
    values: list[int] = []
    for a, b in _PERMS:
        best = _MASK32
        for h in unique:
            v = ((a * h + b) % _PRIME) & _MASK32
            if v < best:
                best = v
        values.append(best)
    return Signature(values=tuple(values))


# ---------------------------------------------------------------- alignment


def align(
    pairs: list[tuple[Span, Span]],
    source: Source,
    text: str,
    source_text: str = "",
    doc_similarity: float = 0.0,
    max_gap: int = 60,
    min_span_chars: int = 60,
) -> list[Match]:
    """Merge shared fingerprints into contiguous, highlightable matches.

    Fingerprints from a copied passage arrive as a run of nearby spans. Sorting
    and merging anything separated by less than `max_gap` characters is what
    lets a match survive a changed word or two mid-sentence, and what turns
    scattered hits into one highlight a reader can act on.

    Runs shorter than `min_span_chars` are dropped: a single shared phrase is
    not evidence of anything, and reporting those is how a similarity score
    gets padded into a number nobody trusts.
    """
    if not pairs:
        return []

    ordered = sorted(pairs, key=lambda p: p[0].start)
    groups: list[list[tuple[Span, Span]]] = [[ordered[0]]]
    for pair in ordered[1:]:
        if pair[0].start - groups[-1][-1][0].end <= max_gap:
            groups[-1].append(pair)
        else:
            groups.append([pair])

    matches: list[Match] = []
    for group in groups:
        span = group[0][0]
        for q_span, _ in group[1:]:
            span = span.merge(q_span)
        if span.length < min_span_chars:
            continue

        src = group[0][1]
        for _, s_span in group[1:]:
            src = src.merge(s_span)

        # Score this passage on its own coverage, not the document's global
        # overlap: a fully copied paragraph inside an otherwise original essay
        # is a strong match even when the documents barely resemble each other.
        density = min(1.0, (len(group) * WINNOW_WINDOW * 4) / max(span.length, 1))
        matches.append(
            Match(
                span=span,
                source=source,
                source_span=src,
                score=round(max(density, doc_similarity), 4),
                kind="verbatim",
                matched_text=text[span.start:span.end],
                source_text=source_text[src.start:src.end] if source_text else "",
            )
        )
    return matches
