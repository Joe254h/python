"""The HTTP surface: auth, credits, submissions, reports, and the dashboard.

Run it:

    python -m apps.api.main                  # real detector, no AI detection
    PROVENANCE_DEMO_MODE=1 python -m apps.api.main   # fabricated reports

Endpoints are deliberately few. Everything the dashboard needs is in
`GET /api/me` and `GET /api/submissions`, so the front end polls two URLs and
holds no derived state of its own -- a balance rendered from anything other
than the ledger is a balance that can be wrong.
"""

from __future__ import annotations

import sqlite3
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from . import auth, credits  # noqa: E402
from .db import connect, transaction  # noqa: E402
from .jobs import Job, Worker, requeue_orphans  # noqa: E402
from .settings import Settings  # noqa: E402

from detector import PIPELINE_ORDER, Stage  # noqa: E402
from detector.extract import SUPPORTED  # noqa: E402

SETTINGS = Settings()
STATIC = Path(__file__).parent / "static"

CONN: sqlite3.Connection = connect(SETTINGS.db_path)
WORKER = Worker(SETTINGS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(SETTINGS.upload_dir).mkdir(parents=True, exist_ok=True)
    # An in-process queue does not survive a restart. Jobs left mid-flight have
    # lost their uploaded file and cannot be resumed, so they are failed with a
    # clear reason and refunded rather than left spinning forever.
    orphaned = requeue_orphans(CONN)
    WORKER.start()
    print("Provenance 0.1.0")
    print(SETTINGS.banner())
    if orphaned:
        print(f"  recovered   {orphaned} interrupted job(s), credits refunded")
    yield
    WORKER.stop()


app = FastAPI(title="Provenance", version="0.1.0", lifespan=lifespan)


# ----------------------------------------------------------------- dependencies


def current_user(provenance_session: str | None = Cookie(default=None)) -> dict:
    user = auth.user_for_token(CONN, provenance_session)
    if user is None:
        raise HTTPException(status_code=401, detail="not signed in")
    return user


# ---------------------------------------------------------------------- models


class SignUp(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=100)
    corpus_consent: bool = True


class SignIn(BaseModel):
    email: str
    password: str


class RedeemBody(BaseModel):
    code: str = Field(min_length=3, max_length=64)


# ------------------------------------------------------------------------ auth


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "provenance_session",
        token,
        httponly=True,
        samesite="lax",
        secure=SETTINGS.secure_cookies,
        max_age=auth.SESSION_DAYS * 24 * 3600,
        path="/",
    )


@app.post("/api/auth/signup")
def signup(body: SignUp, response: Response) -> dict:
    try:
        user_id = auth.create_user(
            CONN,
            body.email,
            body.password,
            body.display_name,
            corpus_consent=body.corpus_consent,
        )
    except auth.AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    credits.grant(
        CONN,
        user_id,
        credits.SIGNUP_GRANT,
        "welcome credits",
        idempotency_key=f"signup:{user_id}",
    )
    _set_cookie(response, auth.start_session(CONN, user_id))
    return {"ok": True}


@app.post("/api/auth/signin")
def signin(body: SignIn, response: Response) -> dict:
    try:
        user_id = auth.authenticate(CONN, body.email, body.password)
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_cookie(response, auth.start_session(CONN, user_id))
    return {"ok": True}


@app.post("/api/auth/signout")
def signout(
    response: Response, provenance_session: str | None = Cookie(default=None)
) -> dict:
    if provenance_session:
        auth.end_session(CONN, provenance_session)
    response.delete_cookie("provenance_session", path="/")
    return {"ok": True}


# --------------------------------------------------------------------- account


@app.get("/api/me")
def me(user: dict = Depends(current_user)) -> dict:
    """Everything the dashboard header and stat cards need, in one call."""
    counts = dict.fromkeys(("processing", "completed", "failed"), 0)
    for row in CONN.execute(
        "SELECT stage, COUNT(*) AS n FROM submission WHERE user_id = ? GROUP BY stage",
        (user["user_id"],),
    ):
        if row["stage"] == Stage.COMPLETE.value:
            counts["completed"] = row["n"]
        elif row["stage"] == Stage.FAILED.value:
            counts["failed"] = row["n"]
        else:
            counts["processing"] += row["n"]

    return {
        "user": user,
        "credits": credits.balance(CONN, user["user_id"]),
        "counts": counts,
        "queue_depth": WORKER.depth,
        "demo_mode": SETTINGS.use_mock_detector,
        "ai_detection_enabled": bool(SETTINGS.calibration_path),
        "cost_per_submission": credits.COST_PER_SUBMISSION,
        "accepted_types": list(SUPPORTED),
        "max_upload_mb": SETTINGS.max_upload_mb,
        "stages": [s.value for s in PIPELINE_ORDER],
    }


@app.get("/api/credits/history")
def credit_history(user: dict = Depends(current_user)) -> dict:
    return {"entries": credits.history(CONN, user["user_id"])}


@app.post("/api/credits/redeem")
def redeem_code(body: RedeemBody, user: dict = Depends(current_user)) -> dict:
    try:
        new_balance = credits.redeem(CONN, user["user_id"], body.code)
    except credits.CodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"credits": new_balance}


# ----------------------------------------------------------------- submissions


@app.post("/api/submissions")
async def create_submission(
    file: UploadFile = File(...), user: dict = Depends(current_user)
) -> JSONResponse:
    """Accept a document, charge one credit, and queue it.

    Order matters and is not arbitrary: validate, then charge, then write the
    row, then queue. Charging before validation would bill people for
    unsupported files; queueing before the row exists would let the worker
    update a submission that is not there yet.
    """
    filename = Path(file.filename or "document").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported file type '{suffix}'. Accepted: {', '.join(SUPPORTED)}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="that file is empty")
    if len(data) > SETTINGS.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"file is larger than {SETTINGS.max_upload_mb}MB",
        )

    submission_id = str(uuid.uuid4())
    try:
        remaining = credits.charge(CONN, user["user_id"], submission_id)
    except credits.InsufficientCredits as exc:
        raise HTTPException(
            status_code=402,
            detail=f"you need {exc.needed} credit but have {exc.balance}",
        ) from exc

    path = Path(SETTINGS.upload_dir) / f"{submission_id}{suffix}"
    path.write_bytes(data)

    with transaction(CONN):
        CONN.execute(
            "INSERT INTO submission (submission_id, user_id, filename, size_bytes, "
            "stage) VALUES (?,?,?,?,?)",
            (submission_id, user["user_id"], filename, len(data), Stage.QUEUED.value),
        )

    WORKER.submit(
        Job(
            submission_id=submission_id,
            user_id=user["user_id"],
            path=path,
            filename=filename,
            corpus_consent=user["corpus_consent"],
        )
    )
    return JSONResponse(
        {"submission_id": submission_id, "credits": remaining}, status_code=201
    )


@app.get("/api/submissions")
def list_submissions(user: dict = Depends(current_user), limit: int = 50) -> dict:
    rows = CONN.execute(
        "SELECT submission_id, filename, stage, error, word_count, similarity, band, "
        "ai_probability, is_mock, created_at, completed_at FROM submission "
        "WHERE user_id = ? ORDER BY created_at DESC, rowid DESC LIMIT ?",
        (user["user_id"], min(limit, 200)),
    ).fetchall()
    return {"submissions": [dict(r) for r in rows]}


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: str, user: dict = Depends(current_user)) -> dict:
    row = CONN.execute(
        "SELECT * FROM submission WHERE submission_id = ? AND user_id = ?",
        (submission_id, user["user_id"]),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="no such submission")

    import json

    payload = dict(row)
    payload["report"] = json.loads(row["report_json"]) if row["report_json"] else None
    payload.pop("report_json", None)
    payload["text"] = row["text_cache"] or ""
    payload.pop("text_cache", None)
    return payload


# ---------------------------------------------------------------------- static


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "version": "0.1.0",
        "queue_depth": WORKER.depth,
        "demo_mode": SETTINGS.use_mock_detector,
    }


if STATIC.exists():
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")


def main() -> None:
    import uvicorn

    import os

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
