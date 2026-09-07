"""Ledger tests, including the Phase 1 gate from the build plan.

The gate: a balance recomputed from the ledger must equal the displayed balance
after 100 randomised submit / fail / refund cycles. That is
`test_phase1_gate_randomised_cycles`.

The other tests here are the specific ways a credit system loses money or
takes money it should not. Each one is a bug that has shipped in real products.
"""

from __future__ import annotations

import random
import sys
import threading
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api import auth, credits  # noqa: E402
from apps.api.db import connect  # noqa: E402


@pytest.fixture()
def conn(tmp_path):
    connection = connect(tmp_path / "test.db")
    yield connection
    connection.close()


@pytest.fixture()
def user(conn):
    return auth.create_user(conn, "a@example.com", "password123", "A")


def test_new_user_starts_at_zero(conn, user):
    assert credits.balance(conn, user) == 0


def test_grant_and_charge(conn, user):
    credits.grant(conn, user, 5, "test")
    assert credits.balance(conn, user) == 5
    credits.charge(conn, user, "sub-1")
    assert credits.balance(conn, user) == 4


def test_charge_is_idempotent(conn, user):
    """A retried worker must not bill twice for the same submission."""
    credits.grant(conn, user, 5, "test")
    for _ in range(4):
        credits.charge(conn, user, "sub-1")
    assert credits.balance(conn, user) == 4


def test_refund_is_idempotent(conn, user):
    credits.grant(conn, user, 5, "test")
    credits.charge(conn, user, "sub-1")
    for _ in range(4):
        credits.refund(conn, user, "sub-1")
    assert credits.balance(conn, user) == 5


def test_refund_without_a_charge_mints_nothing(conn, user):
    """Otherwise a failed job that was never charged creates free credits."""
    credits.grant(conn, user, 2, "test")
    credits.refund(conn, user, "never-charged")
    assert credits.balance(conn, user) == 2


def test_cannot_overdraw(conn, user):
    credits.grant(conn, user, 1, "test")
    credits.charge(conn, user, "sub-1")
    with pytest.raises(credits.InsufficientCredits):
        credits.charge(conn, user, "sub-2")
    assert credits.balance(conn, user) == 0


def test_concurrent_charges_cannot_overdraw(conn, user, tmp_path):
    """The overdraft race: two requests reading the same balance at once.

    Without BEGIN IMMEDIATE around the check-and-debit, both threads see one
    credit and both proceed, and the user gets two jobs for one credit.

    Each thread opens its own connection, which is the real deployment shape --
    the request thread and the worker thread each hold one (see jobs.py). A
    single connection shared across threads would serialise at the driver and
    prove nothing about the lock.
    """
    credits.grant(conn, user, 1, "test")
    successes: list[str] = []
    errors: list[Exception] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def attempt(sub_id: str) -> None:
        own = connect(tmp_path / "test.db")
        try:
            barrier.wait(timeout=5)  # maximise the overlap
            credits.charge(own, user, sub_id)
            with lock:
                successes.append(sub_id)
        except credits.InsufficientCredits as exc:
            with lock:
                errors.append(exc)
        finally:
            own.close()

    threads = [
        threading.Thread(target=attempt, args=(f"sub-{i}",)) for i in range(2)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(successes) == 1, "exactly one charge may succeed"
    assert len(errors) == 1
    assert credits.balance(conn, user) == 0


def test_redeem_code(conn, user):
    credits.create_code(conn, "PROV-TEST-0001", 10)
    assert credits.redeem(conn, user, "prov-test-0001") == 10


def test_code_cannot_be_reused(conn, user):
    credits.create_code(conn, "PROV-TEST-0002", 10)
    credits.redeem(conn, user, "PROV-TEST-0002")
    with pytest.raises(credits.CodeError):
        credits.redeem(conn, user, "PROV-TEST-0002")
    assert credits.balance(conn, user) == 10


def test_unknown_code_rejected(conn, user):
    with pytest.raises(credits.CodeError):
        credits.redeem(conn, user, "NOPE")


def test_one_code_cannot_be_claimed_by_two_users(conn, user):
    other = auth.create_user(conn, "b@example.com", "password123", "B")
    credits.create_code(conn, "PROV-RACE-0001", 7)
    credits.redeem(conn, user, "PROV-RACE-0001")
    with pytest.raises(credits.CodeError):
        credits.redeem(conn, other, "PROV-RACE-0001")
    assert credits.balance(conn, other) == 0


def test_phase1_gate_randomised_cycles(conn, user):
    """The Phase 1 gate, stated as the plan states it.

    A shadow balance is tracked independently of the ledger and compared at the
    end. Any drift -- a double charge, a lost refund, a refund without a charge
    -- shows up as a mismatch.
    """
    rng = random.Random(20260907)
    credits.grant(conn, user, 50, "seed")
    shadow = 50
    charged: list[str] = []

    for _ in range(100):
        action = rng.choice(["submit", "submit", "fail", "grant"])

        if action == "submit":
            sub_id = str(uuid.uuid4())
            try:
                credits.charge(conn, user, sub_id)
                shadow -= 1
                charged.append(sub_id)
            except credits.InsufficientCredits:
                pass

        elif action == "fail" and charged:
            sub_id = charged.pop(rng.randrange(len(charged)))
            credits.refund(conn, user, sub_id)
            shadow += 1
            # A double refund from a retrying worker must change nothing.
            credits.refund(conn, user, sub_id)

        elif action == "grant":
            amount = rng.randint(1, 5)
            credits.grant(conn, user, amount, "top-up")
            shadow += amount

    assert credits.balance(conn, user) == shadow
    assert shadow >= 0


def test_history_is_ordered_newest_first(conn, user):
    credits.grant(conn, user, 5, "first")
    credits.grant(conn, user, 5, "second")
    entries = credits.history(conn, user)
    assert entries[0]["reason"] == "second"


# ----------------------------------------------------------------------- auth


def test_password_round_trip():
    digest, salt = auth.hash_password("correct horse battery")
    assert auth.verify_password("correct horse battery", digest, salt)
    assert not auth.verify_password("wrong", digest, salt)


def test_short_password_rejected():
    with pytest.raises(auth.AuthError):
        auth.hash_password("short")


def test_duplicate_email_rejected(conn):
    auth.create_user(conn, "dup@example.com", "password123")
    with pytest.raises(auth.AuthError):
        auth.create_user(conn, "dup@example.com", "password123")


def test_authenticate_rejects_wrong_password(conn):
    auth.create_user(conn, "c@example.com", "password123")
    with pytest.raises(auth.AuthError):
        auth.authenticate(conn, "c@example.com", "nope")


def test_session_round_trip(conn, user):
    token = auth.start_session(conn, user)
    assert auth.user_for_token(conn, token)["user_id"] == user
    auth.end_session(conn, token)
    assert auth.user_for_token(conn, token) is None


def test_unknown_token_is_none(conn):
    assert auth.user_for_token(conn, "not-a-token") is None
    assert auth.user_for_token(conn, None) is None
