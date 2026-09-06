#!/usr/bin/env python3
"""Validate the 20-example sample and emit training data + provenance.

This script is adversarial towards its own input on purpose. It checks:

  * the think-block format survives in every language (protocol item 3);
  * numbers are identical across all four languages -- a reasoning trace whose
    arithmetic drifts in translation teaches the model wrong arithmetic;
  * every translation actually reads as the language it claims to be, checked
    by the same detector the evaluation uses;
  * no sample question collides with the held-out evaluation set.

A non-zero exit means the sample is not fit to train on.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data" / "sample20"))

from records import SAMPLES, DEFAULT_STATUS          # noqa: E402
from mlr.format_guard import GEMMA4_THINKING as FMT, check_translation  # noqa: E402
from mlr.langid import identify, code_switch_ratio   # noqa: E402

LANGS = ("en", "fr", "sw", "wo")
OUT = Path("data/sample20")
EVAL = Path("data/eval/held_out_v1.jsonl")


def check_no_eval_overlap() -> list[str]:
    if not EVAL.exists():
        return ["held-out eval set not built; run scripts/build_eval_set.py first"]
    eval_qs = {
        json.loads(line)["question"].strip().lower()
        for line in EVAL.read_text(encoding="utf-8").splitlines() if line.strip()
    }
    clashes = []
    for s in SAMPLES:
        for lang in LANGS:
            if s["question"][lang].strip().lower() in eval_qs:
                clashes.append(f"{s['id']}/{lang} duplicates a held-out eval question")
    return clashes


def main() -> int:
    problems: list[str] = []
    lang_flags: list[str] = []
    rows = []

    for s in SAMPLES:
        src = FMT.wrap(s["thinking"]["en"], s["answer"]["en"])

        for lang in LANGS:
            rendered = FMT.wrap(s["thinking"][lang], s["answer"][lang])

            if lang != "en":
                for issue in check_translation(src, rendered, FMT):
                    problems.append(f"{s['id']} [{lang}] {issue}")

            # Does the translation read as the language it claims to be? This
            # is a check on the translator's work, including mine.
            res = identify(s["thinking"][lang])
            if res.top != lang:
                detail = f"detected {res.top}"
                if lang == "wo" and res.top == "fr":
                    detail += f" (fr share {code_switch_ratio(s['thinking'][lang], 'wo', 'fr'):.0%})"
                lang_flags.append(f"{s['id']} [{lang}] reasoning reads as {detail}")

            status = dict(DEFAULT_STATUS)
            rows.append({
                "id": f"{s['id']}-{lang}",
                "sample_id": s["id"],
                "lang": lang,
                "upstream_id": None,          # see records.py provenance note
                "domain": s["domain"],
                "answer_type": s["answer_type"],
                "gold": s["gold"],
                "messages": [
                    {"role": "system", "content": s["system"]},
                    {"role": "user", "content": s["question"][lang]},
                    {"role": "assistant",
                     "thinking": s["thinking"][lang],
                     "content": s["answer"][lang]},
                ],
                "rendered": FMT.wrap(s["thinking"][lang], s["answer"][lang]),
                "verification": status[lang],
                "human_verified": False,      # nothing is signed off yet
                "review_notes": s.get("wo_review", []) if lang == "wo" else [],
            })

    problems.extend(check_no_eval_overlap())

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "sample20.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Per-example provenance log -- protocol item 2 requires knowing exactly
    # what is machine-translated and what a human has verified.
    lines = [
        "# Provenance and verification log",
        "",
        "One row per example per language. `human_verified` is false everywhere:",
        "no native speaker has signed anything off yet, and this file must not",
        "claim otherwise.",
        "",
        "| example | lang | status | human verified | open review points |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        notes = "; ".join(r["review_notes"]) or "-"
        lines.append(
            f"| {r['sample_id']} | {r['lang']} | {r['verification']} | "
            f"{'yes' if r['human_verified'] else 'NO'} | {notes} |"
        )
    (OUT / "PROVENANCE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"records: {len(SAMPLES)}   rows: {len(rows)} ({len(SAMPLES)} x {len(LANGS)} languages)")

    if lang_flags:
        print(f"\nlanguage-identification flags ({len(lang_flags)}):")
        for f_ in lang_flags:
            print(f"  ! {f_}")

    if problems:
        print(f"\nFORMAT/INTEGRITY FAILURES ({len(problems)}):")
        for p in problems:
            print(f"  X {p}")
        return 1

    print("\nformat guard: all 20 x 4 pass (block intact, numbers identical, no delimiter leaks)")
    print(f"wrote {OUT/'sample20.jsonl'} and {OUT/'PROVENANCE.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
