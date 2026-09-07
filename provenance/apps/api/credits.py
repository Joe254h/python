"""The credit ledger: append-only, idempotent, and safe under concurrency.

Three rules, each of which exists because the obvious alternative is wrong.

*Append-only.* The balance is `SUM(delta)`, never a stored column. A stored
balance plus a transaction log is two sources of truth, and they diverge the
first time a process dies between writing one and the other. The plan's Phase 1
gate is exactly this property: a balance recomputed from the ledger must equal
the displayed balance after any sequence of submits, failures and refunds.

*Idempotent.* Every entry carries a unique key. A retried debit with the same
key is a no-op rather than a second charge, which is the only defence against
double-charging when a worker retries or a user double-clicks. The uniqueness
is enforced by the database, not by a check-then-insert in Python, because
check-then-insert races.

*Serialised at the write.* The balance check and the debit happen inside one
`BEGIN IMMEDIATE` transaction. Without it, two concurrent submissions can both
read a balance of one credit and both proceed, and the user gets two jobs for
one credit. This is the classic overdraft bug and it is invisible in testing
until it is expensive in production.
"""

from __future__ import annotations

import sqlite3
import uuid

from .db import transaction

#: What a single document costs. One credit, matching the reference product.
COST_PER_SUBMISSION = 1

#: Credits granted to a new account, so the product is usable on sign-up.
SIGNUP_GRANT = 3


class InsufficientCredits(Exception):
    """Raised when a debit would take a balance below zero."""

    def __init__(self, balance: int, needed: int) -> None:
        self.balance = balance
        self.needed = needed
        super().__init__(f"balance is {balance}, need {needed}")


class CodeError(Exception):
    """A redemption code was unknown or already used."""


def balance(conn: sqlite3.Connection, user_id: str) -> int:
    """Current balance, recomputed from the ledger. The only way to read it."""
    row = conn.execute(
        "SELECT COALESCE(SUM(delta), 0) AS bal FROM credit_ledger WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return int(row["bal"])


def history(conn: sqlite3.Connection, user_id: str, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        "SELECT entry_id, delta, reason, submission_id, created_at "
        "FROM credit_ledger WHERE user_id = ? ORDER BY created_at DESC, rowid DESC "
        "LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def _entry(
    conn: sqlite3.Connection,
    user_id: str,
    delta: int,
    reason: str,
    idempotency_key: str,
    submission_id: str | None = None,
) -> bool:
    """Insert one ledger entry. Returns False if the key was already used."""
    try:
        conn.execute(
            "INSERT INTO credit_ledger "
            "(entry_id, user_id, delta, reason, idempotency_key, submission_id) "
            "VALUES (?,?,?,?,?,?)",
            (
                str(uuid.uuid4()),
                user_id,
                delta,
                reason,
                idempotency_key,
                submission_id,
            ),
        )
        return True
    except sqlite3.IntegrityError:
        # The unique constraint on idempotency_key fired: this exact entry has
        # already been recorded, so the caller's intent is already satisfied.
        return False


def grant(
    conn: sqlite3.Connection,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: str | None = None,
) -> int:
    """Add credits. Returns the new balance."""
    if amount <= 0:
        raise ValueError("grant amount must be positive")
    key = idempotency_key or f"grant:{user_id}:{uuid.uuid4()}"
    with transaction(conn):
        _entry(conn, user_id, amount, reason, key)
    return balance(conn, user_id)


def charge(
    conn: sqlite3.Connection,
    user_id: str,
    submission_id: str,
    amount: int = COST_PER_SUBMISSION,
    reason: str = "submission",
) -> int:
    """Debit for a submission. Raises InsufficientCredits rather than overdrawing.

    The key is derived from the submission id, so charging the same submission
    twice is impossible however many times this is called.
    """
    key = f"charge:{submission_id}"
    with transaction(conn):
        current = int(
            conn.execute(
                "SELECT COALESCE(SUM(delta), 0) AS bal FROM credit_ledger "
                "WHERE user_id = ?",
                (user_id,),
            ).fetchone()["bal"]
        )
        already = conn.execute(
            "SELECT 1 FROM credit_ledger WHERE idempotency_key = ?", (key,)
        ).fetchone()
        if already:
            return current
        if current < amount:
            raise InsufficientCredits(current, amount)
        _entry(conn, user_id, -amount, reason, key, submission_id)
    return balance(conn, user_id)


def refund(
    conn: sqlite3.Connection,
    user_id: str,
    submission_id: str,
    amount: int = COST_PER_SUBMISSION,
    reason: str = "refund: job failed",
) -> int:
    """Return credits for a job that failed.

    A user must not pay for our crash. Keyed on the submission, so a worker
    that retries and fails twice still only refunds once.
    """
    key = f"refund:{submission_id}"
    with transaction(conn):
        charged = conn.execute(
            "SELECT 1 FROM credit_ledger WHERE idempotency_key = ?",
            (f"charge:{submission_id}",),
        ).fetchone()
        # Refunding something never charged would mint credits from nothing.
        if charged:
            _entry(conn, user_id, amount, reason, key, submission_id)
    return balance(conn, user_id)


def create_code(conn: sqlite3.Connection, code: str, credits: int) -> None:
    if credits <= 0:
        raise ValueError("code must carry a positive number of credits")
    with transaction(conn):
        conn.execute(
            "INSERT OR REPLACE INTO redeem_code (code, credits) VALUES (?,?)",
            (code.strip().upper(), credits),
        )


def redeem(conn: sqlite3.Connection, user_id: str, code: str) -> int:
    """Redeem a voucher code. Returns the new balance.

    The claim and the ledger entry are one transaction: two users racing on the
    same code means exactly one of them gets the credits.
    """
    code = code.strip().upper()
    with transaction(conn):
        row = conn.execute(
            "SELECT code, credits, redeemed_by FROM redeem_code WHERE code = ?",
            (code,),
        ).fetchone()
        if row is None:
            raise CodeError("that code is not valid")
        if row["redeemed_by"] is not None:
            raise CodeError("that code has already been used")

        conn.execute(
            "UPDATE redeem_code SET redeemed_by = ?, redeemed_at = datetime('now') "
            "WHERE code = ? AND redeemed_by IS NULL",
            (user_id, code),
        )
        _entry(
            conn,
            user_id,
            int(row["credits"]),
            f"redeemed {code}",
            f"redeem:{code}",
        )
    return balance(conn, user_id)
