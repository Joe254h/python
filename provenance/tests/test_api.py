"""End-to-end HTTP tests, including the Phase 0 gate from the build plan.

The gate: upload a document, watch it move through every state, and open a
report -- with no model installed. `test_phase0_gate_full_round_trip` is that,
against the real detector rather than the mock, because "works with no model
installed" is the claim being tested.

Every test here drives the app the way the browser does: same endpoints, same
cookie, same JSON. The dashboard has no logic these do not exercise.
"""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SOURCE = """Academic integrity is the moral code of academia. It involves honesty in
research, teaching and learning, and it requires that scholars acknowledge the
contributions of others through accurate and complete citation of their work.

Institutions maintain policies that define academic misconduct. These policies
typically cover plagiarism, collusion between students, fabrication of research
data, and the purchase of written work from a third party contractor.

The purpose of these rules is not punishment but the preservation of public
trust in the qualifications that an institution awards to all of its graduates.
"""


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A fresh app against a temporary database, reloaded per test.

    The module holds a connection and a worker at import time, so the modules
    are reimported rather than reconfigured -- reaching in to swap the globals
    would test a shape the deployment never runs in.
    """
    monkeypatch.setenv("PROVENANCE_DB", str(tmp_path / "app.db"))
    monkeypatch.setenv("PROVENANCE_CORPUS", str(tmp_path / "corpus.db"))
    monkeypatch.setenv("PROVENANCE_UPLOADS", str(tmp_path / "uploads"))
    monkeypatch.delenv("PROVENANCE_DEMO_MODE", raising=False)
    monkeypatch.delenv("PROVENANCE_CALIBRATION", raising=False)

    for name in ("apps.api.main", "apps.api.jobs", "apps.api.settings"):
        sys.modules.pop(name, None)
    main = importlib.import_module("apps.api.main")

    with TestClient(main.app) as test_client:
        test_client.app_module = main
        yield test_client


def signup(client, email="joel@example.com", consent=True):
    res = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Joel",
            "corpus_consent": consent,
        },
    )
    assert res.status_code == 200, res.text
    return res


def upload(client, text=SOURCE, name="essay.txt"):
    return client.post(
        "/api/submissions",
        files={"file": (name, text.encode("utf-8"), "text/plain")},
    )


def wait_for(client, submission_id, timeout=15.0):
    """Poll until the job leaves the running stages, as the dashboard does."""
    deadline = time.time() + timeout
    seen: list[str] = []
    while time.time() < deadline:
        row = client.get(f"/api/submissions/{submission_id}").json()
        if row["stage"] not in seen:
            seen.append(row["stage"])
        if row["stage"] in ("complete", "failed"):
            return row, seen
        time.sleep(0.05)
    raise AssertionError(f"job did not finish; stages seen: {seen}")


# --------------------------------------------------------------------- health


def test_health_needs_no_auth(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["demo_mode"] is False


def test_dashboard_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Provenance" in res.text


# ----------------------------------------------------------------------- auth


def test_endpoints_require_a_session(client):
    for path in ("/api/me", "/api/submissions", "/api/credits/history"):
        assert client.get(path).status_code == 401


def test_signup_grants_welcome_credits(client):
    signup(client)
    me = client.get("/api/me").json()
    assert me["credits"] == 3
    assert me["user"]["display_name"] == "Joel"
    assert me["counts"] == {"processing": 0, "completed": 0, "failed": 0}


def test_duplicate_signup_rejected(client):
    signup(client)
    res = client.post(
        "/api/auth/signup",
        json={"email": "joel@example.com", "password": "password123"},
    )
    assert res.status_code == 400


def test_signin_and_signout(client):
    signup(client)
    client.post("/api/auth/signout")
    assert client.get("/api/me").status_code == 401
    res = client.post(
        "/api/auth/signin",
        json={"email": "joel@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    assert client.get("/api/me").status_code == 200


def test_wrong_password_rejected(client):
    signup(client)
    client.post("/api/auth/signout")
    res = client.post(
        "/api/auth/signin",
        json={"email": "joel@example.com", "password": "wrong-password"},
    )
    assert res.status_code == 401


# ----------------------------------------------------------------- the gate


def test_phase0_gate_full_round_trip(client):
    """Upload, move through every stage, open a report -- no model installed."""
    signup(client)

    res = upload(client)
    assert res.status_code == 201, res.text
    submission_id = res.json()["submission_id"]
    assert res.json()["credits"] == 2, "one credit charged on accept"

    row, _ = wait_for(client, submission_id)
    assert row["stage"] == "complete", row.get("error")
    assert row["error"] is None
    assert row["word_count"] > 50
    assert row["similarity"] == 0.0, "nothing in the corpus to match yet"
    assert row["band"] == "ok"
    assert row["is_mock"] == 0, "a real report must never carry the mock flag"

    report = row["report"]
    assert report is not None
    assert report["ai_probability"] is None, "AI detection not configured: not run"
    assert len(report["timings_ms"]) == 9, "all nine stages recorded"
    assert row["text"], "extracted text is kept so the viewer can highlight it"

    me = client.get("/api/me").json()
    assert me["counts"]["completed"] == 1
    assert me["counts"]["processing"] == 0


def test_second_submission_matches_the_first(client):
    """The product's actual job, over HTTP."""
    signup(client)
    first = upload(client, SOURCE, "original.txt").json()["submission_id"]
    wait_for(client, first)

    edited = SOURCE.replace("moral code", "ethical code")
    second = upload(client, edited, "copy.txt").json()["submission_id"]
    row, _ = wait_for(client, second)

    assert row["stage"] == "complete"
    assert row["similarity"] > 0.8, f"got {row['similarity']:.1%}"
    assert row["band"] == "stop"

    sources = row["report"]["sources"]
    assert sources, "the matching source must be listed"
    assert all(s["anonymised"] for s in sources), "internal sources are anonymised"


def test_declining_consent_keeps_the_document_out_of_the_corpus(client):
    signup(client, consent=False)
    first = upload(client, SOURCE, "a.txt").json()["submission_id"]
    wait_for(client, first)
    second = upload(client, SOURCE, "b.txt").json()["submission_id"]
    row, _ = wait_for(client, second)
    assert row["similarity"] == 0.0, "an unconsented document must not be matchable"


# ------------------------------------------------------------------- billing


def test_running_out_of_credits_returns_402(client):
    signup(client)
    for i in range(3):
        assert upload(client, SOURCE, f"e{i}.txt").status_code == 201
    res = upload(client, SOURCE, "e4.txt")
    assert res.status_code == 402
    assert "credit" in res.json()["detail"]


def test_unsupported_file_type_is_not_charged(client):
    signup(client)
    res = client.post(
        "/api/submissions",
        files={"file": ("notes.rtf", b"some text", "application/rtf")},
    )
    assert res.status_code == 400
    assert client.get("/api/me").json()["credits"] == 3, "no credit taken"


def test_empty_file_is_not_charged(client):
    signup(client)
    res = client.post("/api/submissions", files={"file": ("empty.txt", b"", "text/plain")})
    assert res.status_code == 400
    assert client.get("/api/me").json()["credits"] == 3


def test_failed_extraction_refunds_the_credit(client):
    """A user must never pay for a document we could not read."""
    signup(client)
    res = upload(client, "   \n \n  ", "blank.txt")
    assert res.status_code == 201
    assert res.json()["credits"] == 2

    row, _ = wait_for(client, res.json()["submission_id"])
    assert row["stage"] == "failed"
    assert row["error"]
    assert client.get("/api/me").json()["credits"] == 3, "credit returned"


def test_ledger_records_every_movement(client):
    signup(client)
    upload(client)
    entries = client.get("/api/credits/history").json()["entries"]
    reasons = [e["reason"] for e in entries]
    assert "welcome credits" in reasons
    assert "submission" in reasons
    assert sum(e["delta"] for e in entries) == client.get("/api/me").json()["credits"]


def test_redeem_code_adds_credits(client):
    signup(client)
    from apps.api import credits as credits_module

    credits_module.create_code(client.app_module.CONN, "PROV-GIFT-0001", 25)

    res = client.post("/api/credits/redeem", json={"code": "prov-gift-0001"})
    assert res.status_code == 200
    assert res.json()["credits"] == 28

    again = client.post("/api/credits/redeem", json={"code": "PROV-GIFT-0001"})
    assert again.status_code == 400, "a code may only be used once"


def test_bad_code_rejected(client):
    signup(client)
    assert client.post("/api/credits/redeem", json={"code": "NOPE-NOPE"}).status_code == 400


# ------------------------------------------------------------------ isolation


def test_users_cannot_read_each_others_submissions(client):
    signup(client, "a@example.com")
    submission_id = upload(client).json()["submission_id"]
    wait_for(client, submission_id)

    client.post("/api/auth/signout")
    signup(client, "b@example.com")

    assert client.get(f"/api/submissions/{submission_id}").status_code == 404
    assert client.get("/api/submissions").json()["submissions"] == []


def test_unknown_submission_is_404(client):
    signup(client)
    assert client.get("/api/submissions/does-not-exist").status_code == 404


# ----------------------------------------------------------------- demo mode


def test_demo_mode_marks_every_report(tmp_path, monkeypatch):
    """The rule from the plan, enforced end to end."""
    monkeypatch.setenv("PROVENANCE_DB", str(tmp_path / "demo.db"))
    monkeypatch.setenv("PROVENANCE_CORPUS", str(tmp_path / "demo-corpus.db"))
    monkeypatch.setenv("PROVENANCE_UPLOADS", str(tmp_path / "demo-uploads"))
    monkeypatch.setenv("PROVENANCE_DEMO_MODE", "1")

    for name in ("apps.api.main", "apps.api.jobs", "apps.api.settings"):
        sys.modules.pop(name, None)
    main = importlib.import_module("apps.api.main")

    with TestClient(main.app) as demo_client:
        signup(demo_client)
        assert demo_client.get("/api/me").json()["demo_mode"] is True

        submission_id = upload(demo_client).json()["submission_id"]
        row, _ = wait_for(demo_client, submission_id)
        assert row["stage"] == "complete"
        assert row["is_mock"] == 1
        assert "FABRICATED" in row["report"]["detector_versions"]["warning"]
