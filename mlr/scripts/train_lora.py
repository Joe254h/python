#!/usr/bin/env python3
"""QLoRA fine-tune entrypoint. Same code path on HPC, Colab and Kaggle.

HPC:
    python scripts/train_lora.py --data data/sample20/sample20.jsonl \
        --base google/gemma-4-E4B-it --out artifacts/adapter --epochs 3

Colab / Kaggle notebooks call main() with the same arguments, so there is one
implementation to keep correct rather than three that drift apart.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mlr.data import load_training_rows, UnverifiedDataError   # noqa: E402
from mlr.training import LoraSettings, TrainSettings           # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="QLoRA fine-tune Gemma 4 for four-language reasoning.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--data", default="data/sample20/sample20.jsonl",
                   help="training rows (JSONL, as emitted by build_sample.py)")
    p.add_argument("--base", default="google/gemma-4-E4B-it", help="base model id")
    p.add_argument("--out", default="artifacts/adapter", help="adapter output dir")
    p.add_argument("--languages", default="en,fr,sw,wo")
    p.add_argument("--epochs", type=float, default=3.0)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=8)
    p.add_argument("--max-seq-len", type=int, default=1024)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--val-fraction", type=float, default=0.2)
    p.add_argument("--device-map", choices=("single", "auto"), default="single",
                   help="single pins the model to GPU 0 (right for a 4-bit E4B); "
                        "auto shards across all visible GPUs, which is slower and "
                        "only needed if the model genuinely does not fit")
    p.add_argument("--no-4bit", action="store_true",
                   help="plain LoRA in bf16 instead of QLoRA (needs more VRAM)")
    p.add_argument("--fp16", action="store_true",
                   help="use fp16 instead of bf16 (older GPUs, e.g. Kaggle P100)")
    p.add_argument(
        "--allow-unverified", action="store_true",
        help="train on rows no native speaker has signed off. This is a "
             "PIPELINE TEST ONLY -- the choice is written into the model card "
             "and such a run must not be reported as a result.",
    )
    p.add_argument("--no-eval", action="store_true",
                   help="skip per-epoch evaluation. Evaluation is the memory "
                        "peak on a large-vocabulary model; use this if it will "
                        "not fit even with prediction_loss_only")
    p.add_argument("--dry-run", action="store_true",
                   help="prepare and report the corpus, then stop before loading the model")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        corpus = load_training_rows(
            args.data,
            languages=tuple(args.languages.split(",")),
            allow_unverified=args.allow_unverified,
            val_fraction=args.val_fraction,
            seed=args.seed,
        )
    except UnverifiedDataError as exc:
        print(f"\nREFUSED: {exc}\n", file=sys.stderr)
        return 2

    print("=== corpus ===")
    print(corpus.summary())

    if args.dry_run:
        print("\n--dry-run: stopping before the model is loaded.")
        return 0

    cfg = TrainSettings(
        base_model=args.base,
        output_dir=args.out,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        max_seq_len=args.max_seq_len,
        seed=args.seed,
        load_in_4bit=not args.no_4bit,
        device_map=args.device_map,
        eval_during_training=not args.no_eval,
        bf16=not args.fp16,
        lora=LoraSettings(r=args.lora_r, alpha=args.lora_alpha),
    )

    from mlr.training import train           # heavy imports happen here
    card = train(corpus, cfg)
    print(f"\ndata fingerprint: {card['data']['fingerprint']}")
    if card["data"]["trained_on_unverified_data"]:
        print("\n*** This adapter was trained on UNVERIFIED data. "
              "Pipeline test only -- do not report these numbers. ***")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
