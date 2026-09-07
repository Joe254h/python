"""The worker: a queue, a thread, and the stage machine.

Analysis never runs inside a request. Extraction plus fingerprinting takes
seconds on a long document and Binoculars takes considerably longer, so a
synchronous endpoint would hit a proxy timeout on every real submission. The
dashboard's "In Processing" card exists precisely because this is asynchronous.

For Phase 0 the queue is `queue.Queue` and the worker is a daemon thread in the
same process. That is a deliberate choice, not a shortcut deferred: it means
`python -m apps.api.main` is the entire runtime, with no Redis to start, and
every free hosting tier will run it. The `Worker` interface is the same one an
arq or Celery worker presents, so Phase 3's move to a separate process is a
swap of this file, not of its callers.

What this file must get right, and what a queue library would not do for us, is
the failure path. A job that raises has to (1) land in the `failed` stage with
its error recorded, and (2) refund the credit. A user must never pay for our
crash, and a worker that dies silently while holding a debit is the bug that
loses the most trust the fastest.
"""

from __future__ import annotations

import json
import queue
import sqlite3
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import credits
from .db import transaction
from .settings import Settings

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from detector import (  # noqa: E402
    Corpus,
    ExtractionError,
    MockDetector,
    Pipeline,
    Stage,
    extract,
    load_detector,
)


@dataclass
class Job:
    submission_id: str
    user_id: str
    path: Path
    filename: str
    corpus_consent: bool


class Worker:
    """Consumes submissions and writes reports back to the database.

    One connection per worker thread. SQLite in WAL mode handles a writer plus
    concurrent readers, which is exactly this shape: the web request thread
    reads, the worker writes.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.queue: queue.Queue[Job | None] = queue.Queue()
        self.thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._conn: sqlite3.Connection | None = None
        self._corpus: Corpus | None = None
        self._pipeline: Pipeline | None = None
        self._mock = MockDetector(delay_s=settings.mock_stage_delay_s)

    # ----------------------------------------------------------------- setup

    def _resources(self) -> tuple[sqlite3.Connection, Pipeline]:
        """Lazily build per-thread resources.

        SQLite connections are not safe to share across threads, so the worker
        opens its own rather than borrowing the app's.
        """
        if self._conn is None:
            from .db import connect

            self._conn = connect(self.settings.db_path)
        if self._pipeline is None:
            self._corpus = Corpus(self.settings.corpus_path)
            self._pipeline = Pipeline(
                corpus=self._corpus,
                ai_detector=load_detector(self.settings.calibration_path),
            )
        return self._conn, self._pipeline

    def start(self) -> None:
        if self.thread is not None:
            return
        self.thread = threading.Thread(target=self._loop, daemon=True, name="worker")
        self.thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.queue.put(None)
        if self.thread is not None:
            self.thread.join(timeout=5)

    def submit(self, job: Job) -> None:
        self.queue.put(job)

    @property
    def depth(self) -> int:
        return self.queue.qsize()

    # ------------------------------------------------------------------ loop

    def _loop(self) -> None:
        while not self._stop.is_set():
            job = self.queue.get()
            if job is None:
                break
            try:
                self._run(job)
            except Exception:  # noqa: BLE001 - the worker must never die
                traceback.print_exc()
            finally:
                self.queue.task_done()

    def _set_stage(self, conn: sqlite3.Connection, submission_id: str, stage: Stage) -> None:
        with transaction(conn):
            conn.execute(
                "UPDATE submission SET stage = ? WHERE submission_id = ?",
                (stage.value, submission_id),
            )

    def _run(self, job: Job) -> None:
        conn, pipeline = self._resources()
        try:
            self._set_stage(conn, job.submission_id, Stage.EXTRACT)
            doc = extract(job.path)

            if self.settings.use_mock_detector:
                report = self._mock.run(job.submission_id, doc, title=job.filename)
                for stage in (
                    Stage.NORMALISE, Stage.SEGMENT, Stage.FINGERPRINT,
                    Stage.RETRIEVE, Stage.ALIGN, Stage.AI_SCORE,
                    Stage.CALIBRATE, Stage.RENDER,
                ):
                    self._set_stage(conn, job.submission_id, stage)
            else:
                report = pipeline.run(
                    job.submission_id,
                    doc,
                    title=job.filename,
                    # A user who has not consented still gets their report; their
                    # document simply does not join the corpus others are
                    # searched against.
                    add_to_corpus=job.corpus_consent,
                    progress=lambda s: self._set_stage(conn, job.submission_id, s),
                )

            with transaction(conn):
                conn.execute(
                    "UPDATE submission SET stage = ?, word_count = ?, similarity = ?, "
                    "band = ?, ai_probability = ?, is_mock = ?, report_json = ?, "
                    "text_cache = ?, completed_at = datetime('now'), error = NULL "
                    "WHERE submission_id = ?",
                    (
                        Stage.COMPLETE.value,
                        report.word_count,
                        report.similarity,
                        report.band.value,
                        report.ai_probability,
                        int(report.is_mock),
                        report.to_json(),
                        doc.text,
                        job.submission_id,
                    ),
                )

        except ExtractionError as exc:
            self._fail(conn, job, str(exc))
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self._fail(conn, job, f"internal error: {exc.__class__.__name__}")
        finally:
            # The upload is transient. The extracted text is kept for the report
            # viewer; the original file is not needed again and holding student
            # work on disk without a reason is a liability, not a feature.
            try:
                job.path.unlink(missing_ok=True)
            except OSError:
                pass

    def _fail(self, conn: sqlite3.Connection, job: Job, message: str) -> None:
        with transaction(conn):
            conn.execute(
                "UPDATE submission SET stage = ?, error = ?, "
                "completed_at = datetime('now') WHERE submission_id = ?",
                (Stage.FAILED.value, message, job.submission_id),
            )
        credits.refund(conn, job.user_id, job.submission_id)


def requeue_orphans(conn: sqlite3.Connection) -> int:
    """Fail any job left mid-flight by a restart, and refund it.

    An in-process queue does not survive a redeploy. Jobs stuck in a running
    stage at startup are unrecoverable -- their uploaded file is gone -- so the
    honest action is to fail them with a clear reason and return the credit,
    rather than leave a user watching a spinner that will never resolve.
    """
    running = [s.value for s in (
        Stage.QUEUED, Stage.EXTRACT, Stage.NORMALISE, Stage.SEGMENT,
        Stage.FINGERPRINT, Stage.RETRIEVE, Stage.ALIGN, Stage.AI_SCORE,
        Stage.CALIBRATE, Stage.RENDER,
    )]
    rows = conn.execute(
        f"SELECT submission_id, user_id FROM submission "
        f"WHERE stage IN ({','.join('?' * len(running))})",
        running,
    ).fetchall()
    for row in rows:
        with transaction(conn):
            conn.execute(
                "UPDATE submission SET stage = ?, error = ?, "
                "completed_at = datetime('now') WHERE submission_id = ?",
                (
                    Stage.FAILED.value,
                    "interrupted by a server restart; your credit was returned",
                    row["submission_id"],
                ),
            )
        credits.refund(conn, row["user_id"], row["submission_id"])
    return len(rows)
