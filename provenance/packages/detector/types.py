"""The vocabulary every stage of the pipeline speaks.

These types are deliberately dumb: dataclasses with offsets and floats, no
behaviour beyond serialisation. Everything interesting happens in the stages
that produce them.

Two decisions here shape the whole project.

First, every span carries character offsets into the *extracted* text, not
into the source file. A PDF has no stable character index, so the extractor
produces one canonical string and records where each page began. Offsets are
into that string from then on, which is what lets the report highlight a
matched passage and name the page it came from.

Second, `AiSignal` reports a probability with an interval and the false
positive rate of the threshold that produced it. It has no `is_ai` field and
never will. Detectors of this kind flag a large fraction of second-language
writing as machine-written, so a boolean here would be a design error with
consequences for real students -- the calling code is forced to render an
estimate because that is the only honest thing to render.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Stage(str, Enum):
    """The nine pipeline stages, which double as job states in the UI."""

    QUEUED = "queued"
    EXTRACT = "extract"
    NORMALISE = "normalise"
    SEGMENT = "segment"
    FINGERPRINT = "fingerprint"
    RETRIEVE = "retrieve"
    ALIGN = "align"
    AI_SCORE = "ai_score"
    CALIBRATE = "calibrate"
    RENDER = "render"
    COMPLETE = "complete"
    FAILED = "failed"


#: Stages in the order the pipeline runs them, excluding terminal states.
PIPELINE_ORDER: tuple[Stage, ...] = (
    Stage.EXTRACT,
    Stage.NORMALISE,
    Stage.SEGMENT,
    Stage.FINGERPRINT,
    Stage.RETRIEVE,
    Stage.ALIGN,
    Stage.AI_SCORE,
    Stage.CALIBRATE,
    Stage.RENDER,
)


class Band(str, Enum):
    """Similarity bands. Deliberately not shared with the AI-detection scale:
    the two measure different things, and merging them is how these tools
    mislead people."""

    OK = "ok"
    WATCH = "watch"
    WARN = "warn"
    STOP = "stop"


def band_for(similarity: float) -> Band:
    """Map an overall similarity fraction (0..1) onto a reporting band."""
    pct = similarity * 100
    if pct < 15:
        return Band.OK
    if pct < 35:
        return Band.WATCH
    if pct < 60:
        return Band.WARN
    return Band.STOP


@dataclass(frozen=True)
class Span:
    """A half-open character range [start, end) into the extracted text."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"invalid span [{self.start}, {self.end})")

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "Span") -> bool:
        return self.start < other.end and other.start < self.end

    def merge(self, other: "Span") -> "Span":
        return Span(min(self.start, other.start), max(self.end, other.end))


@dataclass(frozen=True)
class Source:
    """Something a passage was matched against."""

    source_id: str
    title: str
    #: "internal" for a previous submission, otherwise the corpus name.
    origin: str
    url: str | None = None
    #: Set only for internal matches, so a report can say "another submission"
    #: without leaking whose.
    anonymised: bool = False


@dataclass(frozen=True)
class Match:
    """One aligned passage: a span of the submission, a span of a source."""

    span: Span
    source: Source
    source_span: Span
    #: 0..1. Jaccard estimate for verbatim matches, cosine for paraphrase.
    score: float
    #: "verbatim" or "paraphrase" -- they are found by different machinery and
    #: a reader needs to know which one flagged a passage.
    kind: str
    matched_text: str = ""
    source_text: str = ""


@dataclass(frozen=True)
class AiSignal:
    """A calibrated estimate that a passage was machine-written.

    `probability` is post-calibration. `interval` is the reported band around
    it. `fpr_at_threshold` is the measured false positive rate of the operating
    threshold on the held-out control set -- it belongs in the payload because
    it belongs on the screen.
    """

    span: Span
    probability: float
    interval: tuple[float, float]
    fpr_at_threshold: float
    #: Name of the detector that produced this, e.g. "binoculars/qwen2.5-0.5b".
    detector: str
    #: Raw pre-calibration score, kept for debugging and re-calibration.
    raw_score: float | None = None


@dataclass
class PageBreak:
    """Where a page started in the extracted text. Lets a report say 'page 4'."""

    page: int
    offset: int


@dataclass
class Document:
    """Extracted text plus everything needed to map offsets back to the file."""

    text: str
    page_breaks: list[PageBreak] = field(default_factory=list)
    #: Spans excluded from similarity scoring -- quotations, reference lists.
    #: Kept rather than deleted so offsets stay stable.
    excluded: list[Span] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def page_at(self, offset: int) -> int:
        page = 1
        for br in self.page_breaks:
            if br.offset <= offset:
                page = br.page
            else:
                break
        return page

    def is_excluded(self, span: Span) -> bool:
        return any(span.overlaps(ex) for ex in self.excluded)


@dataclass
class Report:
    """What a completed job produces."""

    document_id: str
    word_count: int
    #: Fraction of scored words inside a matched span, 0..1.
    similarity: float
    band: Band
    matches: list[Match] = field(default_factory=list)
    ai_signals: list[AiSignal] = field(default_factory=list)
    #: Set by MockDetector. The API refuses to serve a report carrying this
    #: flag unless the deployment is explicitly marked as a demo.
    is_mock: bool = False
    detector_versions: dict[str, str] = field(default_factory=dict)
    timings_ms: dict[str, int] = field(default_factory=dict)

    @property
    def sources(self) -> list[Source]:
        """Distinct sources, most-matched first."""
        weight: dict[str, int] = {}
        seen: dict[str, Source] = {}
        for m in self.matches:
            weight[m.source.source_id] = weight.get(m.source.source_id, 0) + m.span.length
            seen[m.source.source_id] = m.source
        return [seen[sid] for sid in sorted(weight, key=lambda s: -weight[s])]

    @property
    def ai_probability(self) -> float | None:
        """Document-level estimate: the length-weighted mean of paragraph
        signals. Returns None when AI detection did not run, which is not the
        same as zero and must not be rendered as zero."""
        if not self.ai_signals:
            return None
        total = sum(s.span.length for s in self.ai_signals)
        if total == 0:
            return None
        return sum(s.probability * s.span.length for s in self.ai_signals) / total

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["band"] = self.band.value
        d["ai_probability"] = self.ai_probability
        d["sources"] = [asdict(s) for s in self.sources]
        return d

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)
