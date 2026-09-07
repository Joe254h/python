"""Password hashing and session tokens, on the standard library.

`hashlib.scrypt` is in the standard library and is a memory-hard KDF, which is
what this needs -- it makes an offline attack against a leaked database
expensive in RAM as well as time, which plain PBKDF2 does not. Parameters are
the interactive-login set from the scrypt paper (N=2^14, r=8, p=1), costing
about 16MB and a few tens of milliseconds per verification.

No third-party dependency, which matters here: an auth library is the last
place to accept a supply-chain risk for convenience, and this is fifty lines.

Sessions are opaque random tokens in a database table rather than signed JWTs.
A token in a table can be revoked; a JWT cannot be, without building the table
anyway. For a product that holds student work, being able to end a session
immediately is worth more than saving a query.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from .db import transaction

SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SESSION_DAYS = 30


class AuthError(Exception):
    """Sign-up or sign-in failed."""


def hash_password(password: str) -> tuple[str, str]:
    """Return (hash_hex, salt_hex)."""
    if len(password) < 8:
        raise AuthError("password must be at least 8 characters")
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P
    )
    return digest.hex(), salt.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    try:
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
        )
    except ValueError:
        return False
    # Constant-time: a timing side channel here leaks the hash a byte at a time.
    return hmac.compare_digest(digest.hex(), hash_hex)


def create_user(
    conn: sqlite3.Connection,
    email: str,
    password: str,
    display_name: str = "",
    corpus_consent: bool = True,
) -> str:
    email = email.strip().lower()
    if "@" not in email or len(email) < 5:
        raise AuthError("that does not look like an email address")

    digest, salt = hash_password(password)
    user_id = str(uuid.uuid4())
    try:
        with transaction(conn):
            conn.execute(
                "INSERT INTO user (user_id, email, display_name, password_hash, "
                "password_salt, corpus_consent) VALUES (?,?,?,?,?,?)",
                (
                    user_id,
                    email,
                    display_name.strip() or email.split("@")[0],
                    digest,
                    salt,
                    int(corpus_consent),
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise AuthError("an account with that email already exists") from exc
    return user_id


def authenticate(conn: sqlite3.Connection, email: str, password: str) -> str:
    row = conn.execute(
        "SELECT user_id, password_hash, password_salt FROM user WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    # Same error either way: distinguishing them tells an attacker which
    # addresses have accounts.
    if row is None or not verify_password(
        password, row["password_hash"], row["password_salt"]
    ):
        raise AuthError("email or password is incorrect")
    return row["user_id"]


def start_session(conn: sqlite3.Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with transaction(conn):
        conn.execute(
            "INSERT INTO session (token, user_id, expires_at) VALUES (?,?,?)",
            (token, user_id, expires.isoformat()),
        )
    return token


def user_for_token(conn: sqlite3.Connection, token: str | None) -> dict | None:
    if not token:
        return None
    row = conn.execute(
        "SELECT u.user_id, u.email, u.display_name, u.is_admin, u.corpus_consent, "
        "s.expires_at FROM session s JOIN user u ON u.user_id = s.user_id "
        "WHERE s.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        end_session(conn, token)
        return None
    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "is_admin": bool(row["is_admin"]),
        "corpus_consent": bool(row["corpus_consent"]),
    }


def end_session(conn: sqlite3.Connection, token: str) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM session WHERE token = ?", (token,))
