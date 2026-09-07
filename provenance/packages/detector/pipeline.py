"""The nine stages, in order, producing a Report.

This is the only place that knows the pipeline's shape. The API imports it, the
worker imports it, tests import it; none of them reimplement the order or the
scoring rule.

The similarity number deserves a note, because it is the number everyone reads
and the one most easily inflated. It is the fraction of *scored* words that
fall inside at least one matched span. Overlapping matches from different
sources are unioned before counting, so a passage found in three places counts
once -- without that, a widely quoted sentence alone can push a report past
50% and the score stops meaning anything. Quotations and the reference list are
removed from both the numerator and the denominator, so padding a paper with
block quotes neither helps nor hurts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from .aidetect import AiDetector, NullAiDetector, UncalibratedError
from .corpus import Corpus
from .fingerprint import minhash, winnow
from .segment import SHINGLE_SIZE, mark_exclusions, shingles, words
from .types import (
    PIPELINE_ORDER,
    Document,
    Match,
    Report,
    Span,
    Stage,
    band_for,
)

ProgressFn = Callable[[Stage], None]


def union_length(spans: list[Span]) -> int:
    """Total characters covered, counting overlaps once."""
    if not spans:
        return 0
    ordered = sorted(spans, key=lambda s: s.start)
    total = 0
    cur_start, cur_end = ordered[0].start, ordered[0].end
    for span in ordered[1:]:
        if span.start <= cur_end:
            cur_end = max(cur_end, span.end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = span.start, span.end
    return total + (cur_end - cur_start)


def matched_word_count(doc: Document, matches: list[Match]) -> int:
    """Scored words lying inside the union of all matched spans."""
    if not matches:
        return 0
    covered = sorted(
        (m.span for m in matches if not doc.is_excluded(m.span)),
        key=lambda s: s.start,
    )
    if not covered:
        return 0

    merged: list[Span] = [covered[0]]
    for span in covered[1:]:
        if span.start <= merged[-1].end:
            merged[-1] = merged[-1].merge(span)
        else:
            merged.append(span)

    count = 0
    i = 0
    for _word, span in words(doc.text):
        if doc.is_excluded(span):
            continue
        while i < len(merged) and merged[i].end <= span.start:
            i += 1
        if i < len(merged) and merged[i].start <= span.start < merged[i].end:
            count += 1
    return count


@dataclass
class Pipeline:
    """Runs a document through every stage and returns a Report.

    `corpus` is required; `ai_detector` defaults to the null one, which means a
    fresh deployment produces similarity reports with AI detection marked as
    not run. That is the correct Phase 0 behaviour and the correct behaviour
    for any deployment that has not fitted a calibration.
    """

    corpus: Corpus
    ai_detector: AiDetector | None = None
    exclude_quotes: bool = True
    exclude_references: bool = True

    def __post_init__(self) -> None:
        if self.ai_detector is None:
            self.ai_detector = NullAiDetector()

    def run(
        self,
        doc_id: str,
        doc: Document,
        title: str = "",
        add_to_corpus: bool = True,
        progress: ProgressFn | None = None,
    ) -> Report:
        timings: dict[str, int] = {}

        def mark(stage: Stage, started: float) -> None:
            timings[stage.value] = int((time.perf_counter() - started) * 1000)
            if progress is not None:
                progress(stage)

        # 01 extract -- done by the caller, which owns the file. Recorded so the
        # UI's stage list matches the pipeline's.
        t = time.perf_counter()
        mark(Stage.EXTRACT, t)

        # 02 normalise -- decide what will not be scored.
        t = time.perf_counter()
        if self.exclude_quotes or self.exclude_references:
            mark_exclusions(
                doc,
                exclude_quotes=self.exclude_quotes,
                exclude_references=self.exclude_references,
            )
        mark(Stage.NORMALISE, t)

        # 03 segment -- shingles for retrieval.
        t = time.perf_counter()
        grams = shingles(doc.text, SHINGLE_SIZE, exclude=doc.excluded)
        mark(Stage.SEGMENT, t)

        # 04 fingerprint -- winnowed selection plus a document-level signature.
        t = time.perf_counter()
        fingerprints = winnow(grams)
        signature = minhash(grams)
        mark(Stage.FINGERPRINT, t)

        # 05 retrieve + 06 align
        t = time.perf_counter()
        matches = self.corpus.search(
            doc,
            fingerprints=fingerprints,
            signature=signature,
            exclude_id=doc_id,
        )
        mark(Stage.RETRIEVE, t)
        t = time.perf_counter()
        mark(Stage.ALIGN, t)

        # 07 ai_score + 08 calibrate
        t = time.perf_counter()
        try:
            signals = self.ai_detector.score(doc)
        except UncalibratedError:
            # A detector without a calibration reports nothing rather than
            # failing the whole job -- the similarity half of the report is
            # still valid and still worth delivering.
            signals = []
        mark(Stage.AI_SCORE, t)
        t = time.perf_counter()
        mark(Stage.CALIBRATE, t)

        # 09 render
        t = time.perf_counter()
        scored_words = sum(
            1 for _w, span in words(doc.text) if not doc.is_excluded(span)
        )
        matched = matched_word_count(doc, matches)
        similarity = (matched / scored_words) if scored_words else 0.0

        report = Report(
            document_id=doc_id,
            word_count=scored_words,
            similarity=similarity,
            band=band_for(similarity),
            matches=matches,
            ai_signals=signals,
            is_mock=False,
            detector_versions={
                "similarity": f"winnow-{SHINGLE_SIZE}gram",
                "ai": getattr(self.ai_detector, "name", "none"),
                "corpus_size": str(self.corpus.size()),
            },
        )
        mark(Stage.RENDER, t)
        report.timings_ms = timings

        # Added after scoring, never before: a document must not match itself.
        if add_to_corpus:
            self.corpus.add(
                doc_id,
                doc,
                title=title or doc_id,
                origin="internal",
                fingerprints=fingerprints,
                signature=signature,
            )

        return report


__all__ = ["Pipeline", "PIPELINE_ORDER", "union_length", "matched_word_count"]
