"""A detector that produces a complete, obviously-fake report with no models.

The point of this file is that the entire product -- upload, queue, credit
ledger, stage transitions, report viewer, PDF export -- can be finished and
demonstrated before a single model weight is downloaded. Every later phase is
then a swap behind an interface that already exists and is already exercised.

`mlr`'s MockBackend docstring makes the argument this file inherits: a mock is
not a toy, it is how you verify the harness detects what it claims to detect.
The same rule applies here with one addition -- every report this produces
carries `is_mock=True`, and the API refuses to serve such a report unless the
deployment sets PROVENANCE_DEMO_MODE. A fabricated similarity score that
escaped into a real report would be worse than no product at all.
"""

from __future__ import annotations

import hashlib
import time

from .segment import paragraphs, sentences, words
from .types import (
    AiSignal,
    Band,
    Document,
    Match,
    Report,
    Source,
    Span,
    band_for,
)

MOCK_SOURCES = [
    Source(
        source_id="mock-internal-1",
        title="Another submission in this institution",
        origin="internal",
        anonymised=True,
    ),
    Source(
        source_id="mock-wikipedia-1",
        title="Wikipedia — Academic integrity",
        origin="wikipedia",
        url="https://en.wikipedia.org/wiki/Academic_integrity",
    ),
    Source(
        source_id="mock-core-1",
        title="Detecting textual reuse in scholarly writing (CORE)",
        origin="core",
        url="https://core.ac.uk/search?q=textual+reuse",
    ),
]


class MockDetector:
    """Deterministic fake results, derived from the document's own hash.

    Determinism matters: the same upload must produce the same demo report
    twice, or nobody can tell a UI bug from a mock being random.
    """

    name = "mock"

    def __init__(self, delay_s: float = 0.0) -> None:
        #: Optional per-stage sleep, so the dashboard's progress states are
        #: visible when demonstrating rather than flashing past.
        self.delay_s = delay_s

    def _seed(self, doc: Document) -> int:
        digest = hashlib.blake2b(doc.text.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big")

    def run(self, doc_id: str, doc: Document, title: str = "") -> Report:
        seed = self._seed(doc)
        sent_spans = sentences(doc.text)
        word_count = len(words(doc.text))

        # Flag a stable, hash-chosen subset of sentences.
        matches: list[Match] = []
        if sent_spans:
            stride = 3 + (seed % 4)
            for i in range(0, len(sent_spans), stride):
                span = sent_spans[i]
                if span.length < 60:
                    continue
                source = MOCK_SOURCES[(seed + i) % len(MOCK_SOURCES)]
                matches.append(
                    Match(
                        span=span,
                        source=source,
                        source_span=Span(0, span.length),
                        score=0.55 + ((seed >> i % 32) % 40) / 100,
                        kind="verbatim" if i % 2 == 0 else "paraphrase",
                        matched_text=doc.text[span.start:span.end],
                        source_text="[mock] no real source text was retrieved",
                    )
                )

        matched_chars = sum(m.span.length for m in matches)
        similarity = min(0.92, matched_chars / max(len(doc.text), 1))

        # AI signals are emitted with an honest interval and a stated FPR, in
        # the same shape a real detector produces, so the UI is built against
        # the real contract rather than a simplified one.
        signals: list[AiSignal] = []
        for j, span in enumerate(paragraphs(doc.text)):
            p = ((seed >> (j % 24)) % 100) / 100
            signals.append(
                AiSignal(
                    span=span,
                    probability=p,
                    interval=(max(0.0, p - 0.18), min(1.0, p + 0.18)),
                    fpr_at_threshold=0.01,
                    detector="mock",
                    raw_score=None,
                )
            )

        if self.delay_s:
            time.sleep(self.delay_s)

        return Report(
            document_id=doc_id,
            word_count=word_count,
            similarity=similarity,
            band=band_for(similarity),
            matches=matches,
            ai_signals=signals,
            is_mock=True,
            detector_versions={
                "similarity": "mock",
                "ai": "mock",
                "warning": "FABRICATED RESULTS - NOT A REAL ANALYSIS",
            },
        )
