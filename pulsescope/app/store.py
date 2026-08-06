"""In-process job store with disk persistence, so runs survive a restart."""

from __future__ import annotations

import json
import threading
from collections import OrderedDict

from .config import settings
from .models import RunResult


class JobStore:
    def __init__(self, capacity: int = 200) -> None:
        self._jobs: OrderedDict[str, RunResult] = OrderedDict()
        self._lock = threading.Lock()
        self._capacity = capacity
        self._dir = settings.data_dir / "runs"
        self._dir.mkdir(parents=True, exist_ok=True)

    def put(self, run: RunResult) -> None:
        with self._lock:
            self._jobs[run.job_id] = run
            self._jobs.move_to_end(run.job_id)
            while len(self._jobs) > self._capacity:
                self._jobs.popitem(last=False)
        if run.status in {"succeeded", "failed"}:
            path = self._dir / f"{run.job_id}.json"
            path.write_text(run.model_dump_json(indent=2), encoding="utf-8")

    def get(self, job_id: str) -> RunResult | None:
        with self._lock:
            run = self._jobs.get(job_id)
        if run:
            return run
        path = self._dir / f"{job_id}.json"
        if path.exists():
            try:
                return RunResult.model_validate(json.loads(path.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001 - a corrupt file is just a miss
                return None
        return None

    def recent(self, limit: int = 25) -> list[dict]:
        with self._lock:
            runs = list(self._jobs.values())[::-1][:limit]
        return [
            {
                "job_id": r.job_id,
                "prompt": r.query.raw or ", ".join(r.query.subjects),
                "status": r.status,
                "subjects": r.query.subjects,
                "started_at": r.started_at.isoformat(),
                "total_mentions": r.total_mentions,
                "data_quality": r.data_quality,
            }
            for r in runs
        ]


store = JobStore()
