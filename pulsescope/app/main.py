"""FastAPI surface: one launch box in, a full comparison out."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, actors as actor_registry
from .config import settings
from .exporters import mentions_csv, scores_csv
from .models import Metric, Query, RunResult, utcnow
from .orchestrator import run_query
from .query_parser import parse
from .store import store

STATIC = Path(__file__).parent / "static"

app = FastAPI(
    title="PulseScope",
    version=__version__,
    description="Launch a plain-English question, get scraped, scored, ranked answers.",
)


class LaunchRequest(BaseModel):
    prompt: str = Field(..., description="Plain-English launch prompt.")
    subjects: list[str] = Field(default_factory=list, description="Override parsed subjects.")
    metrics: list[Metric] = Field(default_factory=list, description="Override parsed metrics.")
    platforms: list[str] = Field(default_factory=list, description="Restrict to these platforms.")
    region: str | None = None
    lookback_days: int | None = None
    async_run: bool = Field(False, description="Return a job id immediately and poll /api/runs/{id}.")


def _build_query(req: LaunchRequest) -> Query:
    query = parse(req.prompt)
    if req.subjects:
        query.subjects = req.subjects
        query.focus = req.subjects[0]
    if req.metrics:
        query.metrics = req.metrics
    if req.platforms:
        query.platforms = req.platforms
    if req.region:
        query.region = req.region
    if req.lookback_days:
        query.lookback_days = max(7, min(req.lookback_days, 730))
    return query


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "demo_mode": settings.demo_mode,
        "live_actors": sum(1 for a in actor_registry.LIVE_ACTORS if a.available()),
        "total_actors": len(actor_registry.LIVE_ACTORS),
        "time": utcnow().isoformat(),
    }


@app.get("/api/actors")
async def list_actors() -> dict:
    cat = actor_registry.catalogue()
    return {
        "actors": cat,
        "available": sum(1 for a in cat if a["available"]),
        "demo_mode": settings.demo_mode,
    }


@app.get("/api/metrics")
async def list_metrics() -> dict:
    return {"metrics": [{"id": m.value, "label": m.label} for m in Metric]}


@app.post("/api/parse")
async def parse_only(req: LaunchRequest) -> dict:
    query = _build_query(req)
    return {
        "subjects": query.subjects,
        "focus": query.focus,
        "metrics": [m.value for m in query.metrics],
        "region": query.region,
        "lookback_days": query.lookback_days,
        "platforms": query.platforms,
    }


@app.post("/api/launch", response_model=RunResult)
async def launch(req: LaunchRequest, background: BackgroundTasks) -> RunResult:
    query = _build_query(req)
    if not query.subjects:
        raise HTTPException(422, "Could not identify any names in the prompt.")

    job_id = uuid.uuid4().hex[:12]
    if not req.async_run:
        run = await run_query(query, job_id=job_id)
        store.put(run)
        return run

    pending = RunResult(job_id=job_id, query=query, status="queued")
    store.put(pending)

    async def _work() -> None:
        try:
            store.put(await run_query(query, job_id=job_id))
        except Exception as exc:  # noqa: BLE001
            pending.status = "failed"
            pending.warnings.append(str(exc))
            pending.finished_at = utcnow()
            store.put(pending)

    background.add_task(asyncio.create_task, _work())
    return pending


@app.get("/api/runs")
async def recent_runs(limit: int = 25) -> dict:
    return {"runs": store.recent(limit)}


@app.get("/api/runs/{job_id}", response_model=RunResult)
async def get_run(job_id: str) -> RunResult:
    run = store.get(job_id)
    if not run:
        raise HTTPException(404, "Unknown job id.")
    return run


@app.get("/api/runs/{job_id}/scores.csv", response_class=PlainTextResponse)
async def export_scores(job_id: str) -> PlainTextResponse:
    run = store.get(job_id)
    if not run:
        raise HTTPException(404, "Unknown job id.")
    return PlainTextResponse(
        scores_csv(run),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="pulsescope-{job_id}-scores.csv"'},
    )


@app.get("/api/runs/{job_id}/mentions.csv", response_class=PlainTextResponse)
async def export_mentions(job_id: str) -> PlainTextResponse:
    run = store.get(job_id)
    if not run:
        raise HTTPException(404, "Unknown job id.")
    return PlainTextResponse(
        mentions_csv(run),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="pulsescope-{job_id}-mentions.csv"'},
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
