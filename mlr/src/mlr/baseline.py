"""Zero-shot baseline run -- protocol item 1, the "before" measurement.

Run this against untouched Gemma 4 before any training. Without it there is no
way to show the fine-tune improved anything, and a plausible-looking post-
training number proves nothing on its own.

The run is deliberately greedy (temperature 0) so it is reproducible, and the
system prompt is identical across languages so no language gets extra help.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .backends import Backend, baseline_system_prompt
from .evaluation import EvalItem, ItemScore, score_item, aggregate, format_table
from .format_guard import GEMMA4_THINKING, ThinkingFormat


def run_baseline(
    items: Sequence[EvalItem],
    backend: Backend,
    out_dir: str | Path,
    fmt: ThinkingFormat | None = None,
    max_new_tokens: int = 512,
    verbose: bool = True,
) -> dict:
    """Generate on every held-out item, score it, and persist everything.

    Raw generations are written alongside the scores. When a baseline number
    looks surprising the raw text is the only way to tell a real model failure
    from a harness bug, so it is never discarded.
    """
    # Score with the format the backend resolved from its own tokenizer, not a
    # module-level guess. When the two disagree every generation is scored as
    # malformed, which looks like a catastrophic model failure and is not one.
    if fmt is None:
        fmt = getattr(backend, "fmt", GEMMA4_THINKING)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scores: list[ItemScore] = []
    raw_path = out_dir / "raw_generations.jsonl"
    started = time.time()

    with raw_path.open("w", encoding="utf-8") as raw_f:
        for i, item in enumerate(items, 1):
            system = baseline_system_prompt(item.lang)
            t0 = time.time()
            try:
                output = backend.generate(system, item.question, max_new_tokens)
                error = None
            except Exception as exc:                     # noqa: BLE001
                output, error = "", f"{type(exc).__name__}: {exc}"
            elapsed = time.time() - t0

            raw_f.write(json.dumps({
                "id": item.id, "lang": item.lang, "system": system,
                "question": item.question, "gold": item.gold,
                "output": output, "error": error, "seconds": round(elapsed, 2),
            }, ensure_ascii=False) + "\n")

            score = score_item(item, output, fmt)
            if error:
                score.problems.append(error)
            scores.append(score)

            if verbose:
                mark = "OK " if score.fully_ok else "   "
                print(f"{mark}[{i:>3}/{len(items)}] {item.id:<14} {item.lang} "
                      f"correct={score.correct!s:<5} "
                      f"think={score.reasoning_lang:<7} ans={score.answer_lang:<7} "
                      f"{elapsed:>5.1f}s")

    report = aggregate(scores)
    report["backend"] = getattr(backend, "name", "unknown")
    report["total_seconds"] = round(time.time() - started, 1)
    report["n_items"] = len(items)

    (out_dir / "baseline_report.json").write_text(
        json.dumps({"summary": report, "items": [asdict(s) for s in scores]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    table = format_table(report)
    (out_dir / "baseline_table.txt").write_text(table, encoding="utf-8")

    if verbose:
        print("\n" + table)
        print(f"\nraw generations -> {raw_path}")
    return report


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Zero-shot Gemma 4 baseline, 4 languages.")
    p.add_argument("--items", default="data/eval/held_out_v1.jsonl")
    p.add_argument("--out", default="results/baseline")
    p.add_argument("--backend", choices=("transformers", "llamacpp"), default="transformers")
    p.add_argument("--model-id", default="google/gemma-4-E4B-it")
    p.add_argument("--gguf", default="", help="path to a GGUF file for the llamacpp backend")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--threads", type=int, default=4)
    args = p.parse_args()

    from .evaluation import load_items

    items = load_items(args.items)
    if args.backend == "transformers":
        from .backends import TransformersBackend
        backend = TransformersBackend(model_id=args.model_id)
    else:
        from .backends import LlamaCppBackend
        backend = LlamaCppBackend(model_path=args.gguf, n_threads=args.threads)

    run_baseline(items, backend, args.out, max_new_tokens=args.max_new_tokens)


if __name__ == "__main__":
    main()
