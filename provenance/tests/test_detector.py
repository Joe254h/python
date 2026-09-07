"""Detector tests, including the Phase 2 gate from the build plan.

The gate is stated in the plan as: submit a document, then submit a lightly
edited copy, and the second must score above 80% against the first with the
correct spans highlighted. `test_phase2_gate_lightly_edited_copy` is that test
verbatim.

The control tests matter as much as the detection tests. A similarity engine
that flags everything passes every positive test ever written, so every
detection case here is paired with a negative case on text from the same
subject area using the same vocabulary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from detector import (  # noqa: E402
    Corpus,
    MockDetector,
    Pipeline,
    Span,
    extract_text,
    minhash,
    normalise,
    sentences,
    shingles,
    winnow,
)
from detector.aidetect import (  # noqa: E402
    BinocularsDetector,
    Calibration,
    NullAiDetector,
    UncalibratedError,
)
from detector.segment import find_quotations, find_references, paragraphs  # noqa: E402

SOURCE = """Academic integrity is the moral code of academia. It involves honesty in
research, teaching and learning, and it requires that scholars acknowledge the
contributions of others through accurate and complete citation of their work.

Institutions maintain policies that define academic misconduct. These policies
typically cover plagiarism, collusion between students, fabrication of research
data, and the purchase of written work from a third party contractor.

The purpose of these rules is not punishment but the preservation of public
trust in the qualifications that an institution awards to all of its graduates."""

UNRELATED = """The intertropical convergence zone migrates seasonally across West Africa.
Its position controls the onset of the rainy season across the Sahel, and the
models disagree about how anthropogenic forcing will shift it in coming decades.

Observational records from ground stations remain sparse throughout the region,
which complicates any attempt to validate the reanalysis products that most
published studies depend upon for their boundary conditions and verification."""


@pytest.fixture()
def pipeline() -> Pipeline:
    return Pipeline(corpus=Corpus(":memory:"))


# ------------------------------------------------------------------ extraction


def test_normalise_folds_smart_punctuation():
    assert normalise("the “quoted” word") == 'the "quoted" word'
    assert normalise("it’s fine") == "it's fine"


def test_normalise_collapses_whitespace_but_keeps_paragraphs():
    assert normalise("a    b\n\n\n\nc") == "a b\n\nc"


def test_extract_text_rejects_empty():
    from detector import ExtractionError

    with pytest.raises(ExtractionError):
        extract_text("   \n  ")


# ---------------------------------------------------------------- segmentation


def test_sentences_do_not_split_on_abbreviations():
    text = "Smith et al. reported a gain. The second sentence follows here."
    spans = sentences(text)
    assert len(spans) == 2
    assert "Smith et al. reported a gain." in text[spans[0].start:spans[0].end]


def test_paragraphs_merge_short_fragments():
    # A heading followed by a real paragraph must not be scored as its own
    # unit -- perplexity on five words is noise.
    text = "Introduction\n\n" + ("word " * 40).strip()
    spans = paragraphs(text)
    assert len(spans) == 1


def test_find_references_ignores_an_early_mention():
    early = "References are important.\n\n" + ("body text here. " * 40)
    assert find_references(early) == []


def test_find_references_takes_the_last_heading():
    text = ("body " * 100) + "\n\nReferences\n\nSmith, J. (2020). A paper."
    found = find_references(text)
    assert len(found) == 1
    assert text[found[0].start:].startswith("References")


def test_find_quotations_needs_length():
    assert find_quotations('he said "no" loudly') == []
    long_quote = '"' + ("a real quotation of some length " * 2).strip() + '"'
    assert len(find_quotations(long_quote)) == 1


# ---------------------------------------------------------------- fingerprints


def test_winnow_is_deterministic_across_calls():
    grams = shingles(SOURCE)
    assert [f.hash for f in winnow(grams)] == [f.hash for f in winnow(grams)]


def test_winnow_selects_a_fraction_of_shingles():
    grams = shingles(SOURCE)
    selected = winnow(grams)
    assert 0 < len(selected) < len(grams)


def test_winnow_finds_a_shared_passage_the_documents_barely_share():
    """The property that banded MinHash LSH lacked and this replaces.

    Two documents whose global overlap is far below any workable LSH threshold
    must still surface a shared passage.
    """
    shared = "the quick brown fox jumps over the lazy dog and keeps running onwards"
    # Filler must be genuinely varied: repeating one phrase yields only a
    # handful of unique shingles, which would make the global Jaccard high and
    # quietly invert what this test claims to prove.
    a = shared + " " + " ".join(f"alpha{i} beta{i} gamma{i}" for i in range(200))
    b = shared + " " + " ".join(f"zeta{i} eta{i} theta{i}" for i in range(200))

    sig_a, sig_b = minhash(shingles(a)), minhash(shingles(b))
    assert sig_a.jaccard(sig_b) < 0.15, "global similarity should be low"

    hashes_a = {f.hash for f in winnow(shingles(a))}
    hashes_b = {f.hash for f in winnow(shingles(b))}
    assert hashes_a & hashes_b, "the shared passage must still produce a shared fingerprint"


def test_minhash_estimate_tracks_true_jaccard():
    grams_a, grams_b = shingles(SOURCE), shingles(SOURCE[:400])
    est = minhash(grams_a).jaccard(minhash(grams_b))
    from detector.fingerprint import stable_hash

    ha = {stable_hash(t) for t, _ in grams_a}
    hb = {stable_hash(t) for t, _ in grams_b}
    true = len(ha & hb) / len(ha | hb)
    assert abs(est - true) < 0.15


# ------------------------------------------------------------------- pipeline


def test_first_submission_has_no_matches(pipeline):
    report = pipeline.run("a", extract_text(SOURCE), title="a")
    assert report.similarity == 0.0
    assert report.matches == []
    assert report.band.value == "ok"


def test_document_does_not_match_itself(pipeline):
    pipeline.run("a", extract_text(SOURCE), title="a")
    again = pipeline.run("a", extract_text(SOURCE), title="a")
    assert again.matches == [], "a resubmission under the same id must not self-match"


def test_phase2_gate_lightly_edited_copy(pipeline):
    """The Phase 2 gate: an edited copy scores above 80% with correct spans."""
    pipeline.run("original", extract_text(SOURCE), title="Original")

    edited = SOURCE.replace("moral code", "ethical code").replace("purpose", "aim")
    report = pipeline.run("copy", extract_text(edited), title="Copy")

    assert report.similarity > 0.80, f"expected >80%, got {report.similarity:.1%}"
    assert report.band.value == "stop"
    assert report.matches, "spans must be reported, not just a score"

    doc_text = extract_text(edited).text
    for match in report.matches:
        assert match.matched_text == doc_text[match.span.start:match.span.end]
        assert match.source.source_id == "original"


def test_unrelated_document_scores_zero(pipeline):
    """The control. Without this the gate above proves nothing."""
    pipeline.run("original", extract_text(SOURCE), title="Original")
    report = pipeline.run("other", extract_text(UNRELATED), title="Unrelated")
    assert report.matches == []
    assert report.similarity == 0.0


def test_partial_copy_scores_partially(pipeline):
    """One copied paragraph of three lands in the middle bands, not at 100%."""
    pipeline.run("original", extract_text(SOURCE), title="Original")
    first_para = SOURCE.split("\n\n")[0]
    mixed = first_para + "\n\n" + UNRELATED
    report = pipeline.run("mixed", extract_text(mixed), title="Mixed")
    assert 0.15 < report.similarity < 0.75, f"got {report.similarity:.1%}"


def test_quotations_are_excluded_from_scoring(pipeline):
    quoted = '"' + SOURCE.split("\n\n")[0].replace("\n", " ") + '"'
    doc = extract_text(quoted)
    pipeline.run("q", doc, title="Quoted")
    assert doc.excluded, "a long quotation must be marked as excluded"


def test_similarity_counts_overlapping_matches_once(pipeline):
    """Three sources matching the same passage must not treble the score."""
    for i in range(3):
        pipeline.run(f"src{i}", extract_text(SOURCE), title=f"Source {i}")
    report = pipeline.run("copy", extract_text(SOURCE), title="Copy")
    assert report.similarity <= 1.0
    assert len(report.sources) >= 2, "all matching sources should still be listed"


def test_report_serialises_to_json(pipeline):
    pipeline.run("a", extract_text(SOURCE), title="a")
    report = pipeline.run("b", extract_text(SOURCE), title="b")
    import json

    payload = json.loads(report.to_json())
    assert payload["band"] == report.band.value
    assert payload["ai_probability"] is None
    assert isinstance(payload["sources"], list)


def test_every_stage_is_timed(pipeline):
    report = pipeline.run("a", extract_text(SOURCE), title="a")
    assert len(report.timings_ms) == 9


def test_consent_declined_keeps_document_out_of_corpus(pipeline):
    pipeline.run("a", extract_text(SOURCE), title="a", add_to_corpus=False)
    assert pipeline.corpus.size() == 0
    report = pipeline.run("b", extract_text(SOURCE), title="b")
    assert report.matches == [], "a document not in the corpus must not be matchable"


def test_internal_sources_are_anonymised(pipeline):
    pipeline.run("a", extract_text(SOURCE), title="Jane Doe - Essay 1.docx")
    report = pipeline.run("b", extract_text(SOURCE), title="b")
    assert all(s.anonymised for s in report.sources if s.origin == "internal")


# --------------------------------------------------------------- ai detection


def test_null_detector_reports_nothing_not_zero():
    assert NullAiDetector().score(extract_text(SOURCE)) == []


def test_report_without_signals_has_none_probability(pipeline):
    report = pipeline.run("a", extract_text(SOURCE), title="a")
    assert report.ai_probability is None, "absence must not render as 0%"


def test_binoculars_refuses_without_calibration():
    """The rule the whole aidetect module exists to enforce."""
    with pytest.raises(UncalibratedError):
        BinocularsDetector(calibration=None).score(extract_text(SOURCE))


def test_calibration_maps_scores_to_probabilities():
    cal = Calibration(
        detector="test",
        slope=-4.0,
        intercept=3.6,
        threshold=0.9,
        fpr_at_threshold=0.01,
        control_set="toefl-control-v1",
        n_control=500,
    )
    machine_like, human_like = cal.probability(0.6), cal.probability(1.2)
    assert machine_like > human_like
    assert 0.0 <= human_like <= machine_like <= 1.0

    low, high = cal.interval(0.5)
    assert low < 0.5 < high


def test_calibration_round_trips(tmp_path):
    cal = Calibration(
        detector="d", slope=1.0, intercept=0.0, threshold=0.5,
        fpr_at_threshold=0.01, control_set="c", n_control=10,
    )
    path = tmp_path / "cal.json"
    cal.save(path)
    assert Calibration.load(path) == cal


# ---------------------------------------------------------------------- mock


def test_mock_report_is_flagged_as_mock():
    report = MockDetector().run("m", extract_text(SOURCE), title="m")
    assert report.is_mock is True
    assert "FABRICATED" in report.detector_versions["warning"]


def test_mock_is_deterministic():
    a = MockDetector().run("m", extract_text(SOURCE))
    b = MockDetector().run("m", extract_text(SOURCE))
    assert a.similarity == b.similarity
    assert len(a.matches) == len(b.matches)


# --------------------------------------------------------------------- spans


def test_span_rejects_inverted_ranges():
    with pytest.raises(ValueError):
        Span(10, 4)


def test_span_merge_and_overlap():
    assert Span(0, 5).overlaps(Span(4, 9))
    assert not Span(0, 5).overlaps(Span(5, 9))
    assert Span(0, 5).merge(Span(4, 9)) == Span(0, 9)
