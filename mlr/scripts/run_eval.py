#!/usr/bin/env python3
"""Score a model on the held-out set: baseline, fine-tuned, or both.

    # before
    python scripts/run_eval.py --mode baseline --base google/gemma-4-E4B-it
    # after
    python scripts/run_eval.py --mode adapter --adapter artifacts/adapter
    # both, with the comparison the project actually cares about
    python scripts/run_eval.py --mode compare --adapter artifacts/adapter

`compare` writes results/comparison.json, which is what the web app reads.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mlr.evaluation import load_items          # noqa: E402
from mlr.baseline import run_baseline          # noqa: E402


def make_backend(base: str, adapter: str | None, fp16: bool):
    from mlr.backends import TransformersBackend
    backend = TransformersBackend(model_id=base)
    if adapter:
        from peft import PeftModel
        backend.model = PeftModel.from_pretrained(backend.model, adapter)
        backend.model.eval()
        backend.name = f"adapter:{Path(adapter).name}"
    else:
        backend.name = "baseline"
    return backend


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Evaluate on the held-out 4-language set.")
    p.add_argument("--mode", choices=("baseline", "adapter", "compare"), default="compare")
    p.add_argument("--items", default="data/eval/held_out_v1.jsonl")
    p.add_argument("--base", default="google/gemma-4-E4B-it")
    p.add_argument("--adapter", default="artifacts/adapter")
    p.add_argument("--out", default="results")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--limit", type=int, default=0,
                   help="smoke test: N problems PER LANGUAGE, stratified. "
                        "Use --limit 1 to check the whole path end to end in "
                        "minutes before committing to the full run.")
    args = p.parse_args(argv)

    items = load_items(args.items)
    if args.limit:
        # Stratified, not first-N: first-N would be all English and would tell
        # you nothing about the languages the project is actually about.
        seen, kept = {}, []
        for it in items:
            if seen.get(it.lang, 0) < args.limit:
                seen[it.lang] = seen.get(it.lang, 0) + 1
                kept.append(it)
        items = kept
        print(f"--limit {args.limit}: {len(items)} items "
              f"({', '.join(f'{k}={v}' for k, v in sorted(seen.items()))})\n"
              f"SMOKE TEST -- not a baseline. Re-run without --limit for real numbers.")
    out = Path(args.out)
    reports = {}

    if args.mode in ("baseline", "compare"):
        print("=== BASELINE (untouched base model) ===")
        reports["baseline"] = run_baseline(
            items, make_backend(args.base, None, args.fp16),
            out / "baseline", max_new_tokens=args.max_new_tokens)

    if args.mode in ("adapter", "compare"):
        print("\n=== FINE-TUNED (base + LoRA adapter) ===")
        reports["finetuned"] = run_baseline(
            items, make_backend(args.base, args.adapter, args.fp16),
            out / "finetuned", max_new_tokens=args.max_new_tokens)

    if args.mode == "compare":
        card_path = Path(args.adapter) / "model_card.json"
        card = json.loads(card_path.read_text()) if card_path.exists() else {}
        comparison = {
            "base_model": args.base,
            "adapter": args.adapter,
            "model_card": card,
            "baseline": reports["baseline"],
            "finetuned": reports["finetuned"],
            "deltas": {
                lang: {
                    metric: round(
                        reports["finetuned"]["by_language"][lang][metric]
                        - reports["baseline"]["by_language"][lang][metric], 4)
                    for metric in ("reasoning_correct", "reasoning_lang_ok",
                                   "answer_lang_ok", "collapse_to_english",
                                   "correct_and_in_language")
                }
                for lang in reports["baseline"]["by_language"]
            },
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / "comparison.json").write_text(
            json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")

        if card:
            card["evaluation"] = comparison["deltas"]
            card_path.write_text(json.dumps(card, indent=2, ensure_ascii=False),
                                 encoding="utf-8")

        print("\n=== CHANGE (fine-tuned minus baseline) ===")
        for lang, d in comparison["deltas"].items():
            print(f"  {lang}: correct {d['reasoning_correct']:+.0%}  "
                  f"in-language {d['correct_and_in_language']:+.0%}  "
                  f"collapse-EN {d['collapse_to_english']:+.0%}")
        print(f"\nwrote {out/'comparison.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
