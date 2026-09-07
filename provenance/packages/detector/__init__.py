"""Provenance detector: document similarity and AI-writing detection.

Pure Python. Imports nothing from the web application, holds no database
connection of its own beyond the corpus store, and runs on the standard
library alone in its default configuration -- extraction of .txt/.md/.docx,
segmentation, MinHash fingerprinting, LSH retrieval, span alignment and
scoring all work with no third-party package installed.

Optional extras, each degrading to a clear error rather than a wrong answer:

    pymupdf                 PDF extraction
    torch + transformers    Binoculars AI detection

Typical use:

    from detector import Corpus, Pipeline, extract

    corpus = Corpus("data/corpus.db")
    doc = extract("essay.docx")
    report = Pipeline(corpus=corpus).run("sub-1", doc, title="essay.docx")
    print(report.similarity, report.band)
"""

from .aidetect import (
    AiDetector,
    BinocularsDetector,
    Calibration,
    NullAiDetector,
    UncalibratedError,
    load_detector,
)
from .corpus import Corpus
from .extract import ExtractionError, extract, extract_text, normalise
from .fingerprint import (
    Fingerprint,
    FingerprintIndex,
    Signature,
    align,
    minhash,
    winnow,
)
from .mock import MockDetector
from .pipeline import Pipeline, matched_word_count, union_length
from .providers import Router, mock_router
from .segment import mark_exclusions, paragraphs, sentences, shingles, words
from .types import (
    PIPELINE_ORDER,
    AiSignal,
    Band,
    Document,
    Match,
    Report,
    Source,
    Span,
    Stage,
    band_for,
)

__version__ = "0.1.0"

__all__ = [
    "AiDetector", "AiSignal", "Band", "BinocularsDetector", "Calibration",
    "Corpus", "Document", "ExtractionError", "Fingerprint",
    "FingerprintIndex", "Match",
    "MockDetector", "NullAiDetector", "PIPELINE_ORDER", "Pipeline", "Report",
    "Router", "Signature", "Source", "Span", "Stage", "UncalibratedError",
    "align", "band_for", "extract", "extract_text", "load_detector",
    "mark_exclusions", "matched_word_count", "minhash", "mock_router",
    "normalise", "paragraphs", "sentences", "shingles", "union_length",
    "winnow", "words",
]
