#!/usr/bin/env python3
"""PulseScope command line.

    python cli.py "Rate A against B and C in terms of momentum and ground visibility"
    python cli.py --serve
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console          # noqa: E402
from rich.panel import Panel              # noqa: E402
from rich.table import Table              # noqa: E402

from app import actors as actor_registry  # noqa: E402
from app.exporters import mentions_csv, scores_csv  # noqa: E402
from app.orchestrator import run_prompt   # noqa: E402
from app.query_parser import parse        # noqa: E402

console = Console()


def show_actors() -> None:
    table = Table(title="Actors", header_style="bold")
    for col in ("Actor", "Platform", "Needs", "State", "Description"):
        table.add_column(col, overflow="fold")
    for a in actor_registry.catalogue():
        table.add_row(
            a["name"], a["platform"], ", ".join(a["requires"]) or "-",
            "[green]ready[/green]" if a["available"] else f"[yellow]dormant[/yellow] ({a['reason']})",
            a["description"],
        )
    console.print(table)


def render(run) -> None:
    q = run.query
    console.print(Panel(run.summary, title=f"Verdict · job {run.job_id}", border_style="cyan"))

    for w in run.warnings:
        console.print(f"[yellow]! {w}[/yellow]")

    table = Table(title=f"Scoreboard · {run.total_mentions} items · "
                        f"{round(run.data_quality * 100)}% live data", header_style="bold")
    table.add_column("#", justify="right")
    table.add_column("Subject")
    table.add_column("Overall", justify="right")
    for m in q.metrics:
        table.add_column(m.label.replace(" & ", "/"), justify="right")
    table.add_column("Items", justify="right")
    table.add_column("Source")

    for r in run.results:
        source = ("simulated" if r.simulated_share >= 0.999
                  else f"{round((1 - r.simulated_share) * 100)}% live")
        table.add_row(
            str(r.rank),
            r.subject,
            f"[bold]{r.overall}[/bold]",
            *[str(r.metrics[m].score) for m in q.metrics],
            str(r.mention_count),
            source,
        )
    console.print(table)

    for r in run.results:
        best = min(q.metrics, key=lambda m: r.metrics[m].rank)
        worst = max(q.metrics, key=lambda m: r.metrics[m].rank)
        console.print(
            f"  [bold]{r.subject}[/bold]: strongest on {best.label.lower()} "
            f"(#{r.metrics[best].rank}), weakest on {worst.label.lower()} "
            f"(#{r.metrics[worst].rank})"
        )

    errors = [rep for rep in run.actor_reports if rep.status == "error"]
    if errors:
        console.print(f"\n[dim]{len(errors)} actor call(s) failed - use --verbose for detail[/dim]")


def show_log(run) -> None:
    table = Table(title="Run log", header_style="bold")
    for col in ("Actor", "Subject", "Status", "Items", "Detail", "ms"):
        table.add_column(col, overflow="fold")
    for rep in run.actor_reports:
        colour = {"ok": "green", "skipped": "yellow", "error": "red"}[rep.status]
        table.add_row(rep.actor, rep.subject, f"[{colour}]{rep.status}[/{colour}]",
                      str(rep.items), rep.detail or "-", str(rep.elapsed_ms))
    console.print(table)


def main() -> int:
    ap = argparse.ArgumentParser(description="PulseScope - scrape, score and rank from one prompt.")
    ap.add_argument("prompt", nargs="?", help="Plain-English launch prompt.")
    ap.add_argument("--region", default=None, help="Region code, e.g. KE.")
    ap.add_argument("--days", type=int, default=None, help="Lookback window in days.")
    ap.add_argument("--platforms", default="", help="Comma-separated platform filter.")
    ap.add_argument("--json", dest="json_out", metavar="PATH", help="Write the full run as JSON.")
    ap.add_argument("--csv", metavar="PATH", help="Write the scoreboard as CSV.")
    ap.add_argument("--mentions-csv", metavar="PATH", help="Write sample items as CSV.")
    ap.add_argument("--verbose", action="store_true", help="Print the per-actor run log.")
    ap.add_argument("--parse-only", action="store_true", help="Show how the prompt was parsed.")
    ap.add_argument("--actors", action="store_true", help="List actors and exit.")
    ap.add_argument("--serve", action="store_true", help="Start the web UI instead.")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    if args.actors:
        show_actors()
        return 0

    if args.serve:
        import uvicorn

        console.print(f"[cyan]PulseScope UI → http://{args.host}:{args.port}[/cyan]")
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)
        return 0

    if not args.prompt:
        ap.error("give a prompt, or use --serve / --actors")

    if args.parse_only:
        q = parse(args.prompt)
        console.print_json(json.dumps({
            "subjects": q.subjects, "focus": q.focus,
            "metrics": [m.value for m in q.metrics],
            "region": q.region, "locality": q.locality,
            "lookback_days": q.lookback_days,
            "platforms": q.platforms,
        }))
        return 0

    overrides = {}
    if args.region:
        overrides["region"] = args.region
    if args.days:
        overrides["lookback_days"] = args.days
    if args.platforms:
        overrides["platforms"] = [p.strip() for p in args.platforms.split(",") if p.strip()]

    with console.status("[cyan]running actors…", spinner="dots"):
        run = asyncio.run(run_prompt(args.prompt, **overrides))

    render(run)
    if args.verbose:
        show_log(run)

    if args.json_out:
        Path(args.json_out).write_text(run.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]wrote {args.json_out}[/dim]")
    if args.csv:
        Path(args.csv).write_text(scores_csv(run), encoding="utf-8")
        console.print(f"[dim]wrote {args.csv}[/dim]")
    if args.mentions_csv:
        Path(args.mentions_csv).write_text(mentions_csv(run), encoding="utf-8")
        console.print(f"[dim]wrote {args.mentions_csv}[/dim]")

    return 0 if run.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
