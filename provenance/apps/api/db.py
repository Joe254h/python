"""Schema and connection handling.

SQLite by default, and that is a real choice rather than a placeholder. A
single-file database removes the entire "start postgres, start redis, run
migrations" step from a contributor's first ten minutes, and every free hosting
tier that runs a container will run this. The schema is written in ordinary
SQL that Postgres also accepts, so the Phase 3 move is a connection string and
a driver, not a rewrite.

The one thing worth reading closely is `credit_ledger`. It has no balance
column. A balance is a derived quantity -- the sum of every entry -- and
storing it as well would create two sources of truth that drift the first time
a worker crashes between debiting a job and recording it. Reconstructing the
balance on every read is slower and correct, and at the transaction volume of a
credit-based product the difference is not measurable.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    user_id       TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    display_name  TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    -- Consent to the submission being retained in the searchable corpus.
    -- Stored per user because it is a real choice they are entitled to make,
    -- and because a corpus built without it is not one we should be building.
    corpus_consent INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS session (
    token      TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES user(user_id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_session_user ON session(user_id);

-- Append-only. Never updated, never deleted. Balance = SUM(delta).
CREATE TABLE IF NOT EXISTS credit_ledger (
    entry_id       TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES user(user_id) ON DELETE CASCADE,
    delta          INTEGER NOT NULL,
    reason         TEXT NOT NULL,
    -- Makes every write idempotent: a retried debit with the same key is a
    -- no-op rather than a second charge. This is the entire defence against
    -- double-charging a user when a worker retries.
    idempotency_key TEXT NOT NULL UNIQUE,
    submission_id  TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ledger_user ON credit_ledger(user_id);

CREATE TABLE IF NOT EXISTS redeem_code (
    code       TEXT PRIMARY KEY,
    credits    INTEGER NOT NULL,
    redeemed_by TEXT REFERENCES user(user_id),
    redeemed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS submission (
    submission_id TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES user(user_id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    size_bytes    INTEGER NOT NULL,
    stage         TEXT NOT NULL DEFAULT 'queued',
    error         TEXT,
    word_count    INTEGER,
    similarity    REAL,
    band          TEXT,
    ai_probability REAL,
    is_mock       INTEGER NOT NULL DEFAULT 0,
    report_json   TEXT,
    text_cache    TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_submission_user ON submission(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submission_stage ON submission(stage);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with the schema applied and sane concurrency settings.

    `isolation_level=None` puts the driver in autocommit mode, which sounds like
    the opposite of what a ledger wants and is in fact the prerequisite for it.
    In the default mode the driver opens a *deferred* transaction implicitly
    before the first write, so an explicit `BEGIN IMMEDIATE` -- the thing that
    actually prevents the overdraft race -- raises "cannot start a transaction
    within a transaction". Autocommit hands transaction control back to us, and
    `transaction()` below is where it is exercised.

    `timeout` is what makes concurrent writers queue rather than fail: a second
    writer waiting on the lock retries for 30 seconds before giving up.
    """
    path = str(db_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        path, check_same_thread=False, timeout=30.0, isolation_level=None
    )
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block inside one `BEGIN IMMEDIATE` transaction.

    IMMEDIATE takes the write lock at the start rather than on first write, so a
    read-then-write sequence -- check the balance, then debit it -- is atomic
    against other writers. A deferred transaction would let two threads both
    read the same balance before either writes, which is the overdraft bug.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
