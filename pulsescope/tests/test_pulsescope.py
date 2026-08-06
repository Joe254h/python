"""Test suite. Run with: python3 -m pytest tests -q  (or python3 tests/test_pulsescope.py)"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.actors import catalogue                       # noqa: E402
from app.exporters import scores_csv                   # noqa: E402
from app.models import Mention, Metric                 # noqa: E402
from app.nlp.text import keyword_density, sentiment_score, tokenize  # noqa: E402
from app.orchestrator import dedupe, is_relevant, run_prompt         # noqa: E402
from app.query_parser import parse                     # noqa: E402
from app.scoring import score_cohort                   # noqa: E402

EXAMPLE = (
    "Rate Philip Munialo against Moses lupao, Emmanuel waswa, Dawson mudenyo, "
    "peter mukiri, kitur kibiyego,and Nick Biketi, in terms of momentum building, "
    "message clarity and manifest, social media presence and ground visibility."
)


# ------------------------------------------------------------------ parser ---

def test_parses_the_example_prompt():
    q = parse(EXAMPLE)
    assert q.subjects == [
        "Philip Munialo", "Moses Lupao", "Emmanuel Waswa", "Dawson Mudenyo",
        "Peter Mukiri", "Kitur Kibiyego", "Nick Biketi",
    ]
    assert q.focus == "Philip Munialo"
    assert q.metrics == [
        Metric.MOMENTUM, Metric.MESSAGE_CLARITY,
        Metric.SOCIAL_PRESENCE, Metric.GROUND_VISIBILITY,
    ]


def test_bare_on_starts_the_metric_clause():
    q = parse("Compare Safaricom against Airtel Kenya on momentum and social media presence")
    assert q.subjects == ["Safaricom", "Airtel Kenya"]
    assert q.metrics == [Metric.MOMENTUM, Metric.SOCIAL_PRESENCE]


def test_geo_and_time_clauses_are_not_names():
    q = parse("rank Mary Wanjiku, Grace Otieno and Ali Hassan in Bungoma county "
              "on ground visibility over the last 30 days")
    assert q.subjects == ["Mary Wanjiku", "Grace Otieno", "Ali Hassan"]
    assert q.locality == "Bungoma county"
    assert q.lookback_days == 30


def test_country_sets_the_region_code():
    q = parse("analyse Nike versus Adidas in the United States on sentiment")
    assert q.region == "US"
    assert q.subjects == ["Nike", "Adidas"]


def test_defaults_when_no_metrics_named():
    q = parse("compare Jane Doe vs John Smith")
    assert q.subjects == ["Jane Doe", "John Smith"]
    assert len(q.metrics) == 4


def test_platform_filter_only_on_explicit_only():
    assert parse("rate A against B only on tiktok").platforms == ["tiktok"]
    assert parse("rate A against B on tiktok momentum").platforms == []


# --------------------------------------------------------------------- nlp ---

def test_sentiment_direction_and_negation():
    assert sentiment_score("A credible, honest leader with a strong vision") > 0.2
    assert sentiment_score("corrupt, dishonest and a total failure") < -0.2
    assert sentiment_score("the meeting is on Tuesday") == 0.0
    assert sentiment_score("not corrupt") > sentiment_score("corrupt")


def test_keyword_density_families():
    ground = "He held a rally at the village market and toured the ward"
    assert keyword_density(ground, "ground") > keyword_density(ground, "policy")
    policy = "The manifesto pledges bursaries, healthcare and road funding"
    assert keyword_density(policy, "policy") > keyword_density(policy, "ground")


def test_tokenize_drops_stopwords():
    assert "the" not in tokenize("the rally was big")
    assert "rally" in tokenize("the rally was big")


# ---------------------------------------------------------------- pipeline ---

def _mention(subject, text, days_ago, platform="x", likes=10, **kw):
    return Mention(
        subject=subject, platform=platform, actor="test", text=text,
        published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        likes=likes, **kw,
    )


def test_relevance_filter_requires_the_name():
    m = _mention("Philip Munialo", "Munialo addressed the ward meeting", 3)
    assert is_relevant(m, "Philip Munialo")
    assert not is_relevant(_mention("Philip Munialo", "A road was opened today", 3), "Philip Munialo")


def test_dedupe_collapses_repeats():
    a = _mention("X", "same text here", 1)
    b = _mention("X", "same text here", 2)
    assert len(dedupe([a, b])) == 1


def test_momentum_rewards_recent_acceleration():
    rising = [_mention("Rising", "rally in the ward", d) for d in (1, 2, 3, 4, 5, 6, 7, 8)]
    fading = [_mention("Fading", "rally in the ward", d) for d in (70, 72, 74, 76, 78, 80, 82, 84)]
    out = score_cohort({"Rising": rising, "Fading": fading}, [Metric.MOMENTUM], 90)
    by = {r.subject: r.metrics[Metric.MOMENTUM].score for r in out}
    assert by["Rising"] > by["Fading"]


def test_clarity_rewards_consistent_costed_policy():
    focused = [
        _mention("Focused",
                 "Manifesto pledges 12 boreholes for water and 40 bursaries within 6 months", d)
        for d in range(1, 12)
    ]
    vague = [
        _mention("Vague", f"He attended an event and greeted supporters number {d}", d)
        for d in range(1, 12)
    ]
    out = score_cohort({"Focused": focused, "Vague": vague}, [Metric.MESSAGE_CLARITY], 90)
    by = {r.subject: r.metrics[Metric.MESSAGE_CLARITY].score for r in out}
    assert by["Focused"] > by["Vague"]


def test_ground_visibility_rewards_field_activity():
    field = [
        _mention("Field", "Rally at the village market, toured the ward, harambee at church", d,
                 platform="news")
        for d in range(1, 10)
    ]
    online = [
        _mention("Online", "Posted a thread about national policy debate online", d)
        for d in range(1, 10)
    ]
    out = score_cohort({"Field": field, "Online": online}, [Metric.GROUND_VISIBILITY], 90)
    by = {r.subject: r.metrics[Metric.GROUND_VISIBILITY].score for r in out}
    assert by["Field"] > by["Online"]


def test_presence_rewards_breadth_and_engagement():
    broad = [
        _mention("Broad", "campaign update", d, platform=p, likes=500)
        for d, p in enumerate(["x", "facebook", "instagram", "tiktok", "youtube", "x"], start=1)
    ]
    narrow = [_mention("Narrow", "campaign update", d, platform="x", likes=2) for d in range(1, 7)]
    out = score_cohort({"Broad": broad, "Narrow": narrow}, [Metric.SOCIAL_PRESENCE], 90)
    by = {r.subject: r.metrics[Metric.SOCIAL_PRESENCE].score for r in out}
    assert by["Broad"] > by["Narrow"]


def test_scores_stay_inside_bounds_and_rank_consistently():
    corpus = {
        "A": [_mention("A", "rally manifesto bursaries", d) for d in range(1, 20)],
        "B": [_mention("B", "quiet", d) for d in (80, 85)],
        "C": [],
    }
    metrics = [Metric.MOMENTUM, Metric.MESSAGE_CLARITY,
               Metric.SOCIAL_PRESENCE, Metric.GROUND_VISIBILITY]
    out = score_cohort(corpus, metrics, 90)
    assert [r.rank for r in out] == [1, 2, 3]
    for r in out:
        assert 0 < r.overall < 100
        for m in metrics:
            assert 0 < r.metrics[m].score < 100
            assert 1 <= r.metrics[m].rank <= 3


def test_empty_corpus_is_not_a_crash():
    assert score_cohort({}, [Metric.MOMENTUM], 90) == []


# ---------------------------------------------------------- end to end ---

def test_full_run_from_a_prompt():
    run = asyncio.run(run_prompt(EXAMPLE))
    assert run.status == "succeeded"
    assert len(run.results) == 7
    assert run.total_mentions > 0
    assert run.summary
    # Nothing is presented as live unless it is.
    for r in run.results:
        if r.simulated_share > 0:
            assert any("simulated" in w.lower() or "demo" in w.lower() for w in run.warnings)
    csv = scores_csv(run)
    assert csv.startswith("rank,subject,overall,")
    assert len(csv.strip().splitlines()) == 8


def test_run_with_no_subjects_fails_cleanly():
    run = asyncio.run(run_prompt("!!! ???"))
    assert run.status == "failed"
    assert run.warnings


def test_actor_catalogue_reports_credentials():
    cat = catalogue()
    assert cat
    for a in cat:
        assert a["available"] or a["reason"]


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print("\n" + ("all green" if not failures else f"{failures} failing"))
    raise SystemExit(1 if failures else 0)
