#!/usr/bin/env python3
"""Run the evaluation across several GPUs at once.

WHY DATA PARALLEL AND NOT device_map="auto"
-------------------------------------------
Sharding one model across two GPUs (`device_map="auto"`) buys memory, not
speed: the layers still run in sequence, one GPU idling while the other works,
plus PCIe transfers between them. For a 4-bit E4B that already fits in a
single T4 it is strictly slower.

The evaluation is embarrassingly parallel instead -- 48 independent items. So
put a FULL copy of the model on each GPU and give each one half the items.
That is a genuine ~Nx speedup.

It is also numerically identical to the sequential run. Each item is generated
independently with greedy decoding, so which GPU produced it cannot change the
output. That matters here: this is a baseline, and a baseline whose numbers
shift when you change the hardware layout is not a baseline. (Batched
generation would be faster still, but padding can perturb results, so it is
not something to do to a measurement you intend to trust.)

    python scripts/run_eval_parallel.py --mode baseline --base $BASE_MODEL \\
        --out results --gpus 0,1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mlr.evaluation import ItemScore, aggregate, format_table   # noqa: E402


def split_stratified(rows: list[dict], n: int) -> list[list[dict]]:
    """Split items across n shards, balanced per language.

    A naive rows[i::n] would be badly wrong here: the held-out file is ordered
    problem-by-problem with the four languages adjacent, so every other item is
    the same language. Shard 0 would get English and Swahili only. Balance
    within each language group instead, so every shard sees all four and a
    crashed shard costs a slice of each rather than two whole languages.
    """
    shards: list[list[dict]] = [[] for _ in range(n)]
    by_lang: dict[str, list[dict]] = {}
    for row in rows:
        by_lang.setdefault(row["lang"], []).append(row)
    for lang in sorted(by_lang):
        for j, row in enumerate(by_lang[lang]):
            shards[j % n].append(row)
    return shards


def merge_reports(shard_dirs: list[Path], sub: str, dest: Path) -> dict:
    """Recombine per-shard reports into one, as if it had run sequentially."""
    items: list[dict] = []
    raw_lines: list[str] = []
    for d in shard_dirs:
        report = d / sub / "baseline_report.json"
        if not report.exists():
            raise SystemExit(f"shard produced no report: {report}\n"
                             f"Check that shard's output above for the error.")
        items.extend(json.loads(report.read_text(encoding="utf-8"))["items"])
        raw = d / sub / "raw_generations.jsonl"
        if raw.exists():
            raw_lines.extend(raw.read_text(encoding="utf-8").splitlines())

    items.sort(key=lambda r: r["id"])
    scores = [ItemScore(**{k: v for k, v in r.items()
                           if k in ItemScore.__dataclass_fields__}) for r in items]
    report = aggregate(scores)
    report["n_items"] = len(scores)
    report["parallel_shards"] = len(shard_dirs)

    dest.mkdir(parents=True, exist_ok=True)
    (dest / "baseline_report.json").write_text(
        json.dumps({"summary": report, "items": items}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (dest / "baseline_table.txt").write_text(format_table(report), encoding="utf-8")
    if raw_lines:
        (dest / "raw_generations.jsonl").write_text("\n".join(raw_lines) + "\n",
                                                    encoding="utf-8")
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mode", choices=("baseline", "adapter"), default="baseline")
    p.add_argument("--items", default="data/eval/held_out_v1.jsonl")
    p.add_argument("--base", default="google/gemma-4-E4B-it")
    p.add_argument("--adapter", default="artifacts/adapter")
    p.add_argument("--out", default="results")
    p.add_argument("--gpus", default="0,1", help="comma-separated device ids")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--fp16", action="store_true")
    args = p.parse_args(argv)

    gpus = [g.strip() for g in args.gpus.split(",") if g.strip()]
    rows = [json.loads(l) for l in
            Path(args.items).read_text(encoding="utf-8").splitlines() if l.strip()]

    if args.limit:
        seen, kept = {}, []
        for r in rows:
            if seen.get(r["lang"], 0) < args.limit:
                seen[r["lang"]] = seen.get(r["lang"], 0) + 1
                kept.append(r)
        rows = kept

    out = Path(args.out)
    shard_dir = out / "_shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    shards = split_stratified(rows, len(gpus))

    procs, dirs = [], []
    started = time.time()
    for i, (gpu, shard) in enumerate(zip(gpus, shards)):
        items_file = shard_dir / f"items_{i}.jsonl"
        items_file.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in shard) + "\n",
            encoding="utf-8")
        d = shard_dir / f"gpu{gpu}"
        dirs.append(d)

        env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu)
        cmd = [sys.executable, "scripts/run_eval.py", "--mode", args.mode,
               "--items", str(items_file), "--base", args.base,
               "--out", str(d), "--max-new-tokens", str(args.max_new_tokens)]
        if args.mode == "adapter":
            cmd += ["--adapter", args.adapter]
        if args.fp16:
            cmd.append("--fp16")

        counts = {}
        for r in shard:
            counts[r["lang"]] = counts.get(r["lang"], 0) + 1
        print(f"GPU {gpu}: {len(shard)} items "
              f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})")
        log = open(shard_dir / f"gpu{gpu}.log", "w")
        procs.append((gpu, subprocess.Popen(cmd, env=env, stdout=log,
                                            stderr=subprocess.STDOUT), log))

    print(f"\n{len(procs)} processes running, one full model per GPU. "
          f"Live logs: {shard_dir}/gpu*.log\n")

    failed = []
    for gpu, proc, log in procs:
        code = proc.wait()
        log.close()
        tail = (shard_dir / f"gpu{gpu}.log").read_text(encoding="utf-8").splitlines()
        print(f"--- GPU {gpu} finished (exit {code}) ---")
        print("\n".join(tail[-12:]))
        if code != 0:
            failed.append(gpu)

    if failed:
        print(f"\nGPU(s) {failed} failed. Full logs in {shard_dir}.", file=sys.stderr)
        return 1

    sub = "baseline" if args.mode == "baseline" else "finetuned"
    report = merge_reports(dirs, sub, out / sub)
    elapsed = time.time() - started
    print("\n" + "=" * 70)
    print(f"MERGED — {report['n_items']} items across {len(gpus)} GPUs "
          f"in {elapsed/60:.1f} min")
    print("=" * 70)
    print(format_table(report))
    print(f"\n-> {out/sub}/baseline_table.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
