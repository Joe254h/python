#!/usr/bin/env python3
"""Explain a run's format failures before anyone reads its accuracy numbers.

A format failure counts as incorrect. So if generations are being truncated at
the token cap -- a thinking model reasoning past the limit never emits its
closing delimiter -- the correctness figures are a floor, not an estimate, and
the run is partly measuring max_new_tokens rather than the model.

This separates the two: what the parse failures actually were, how close the
outputs ran to the cap, and a sample of the raw text.

    python scripts/diagnose_run.py --run results/baseline
"""

import argparse
import json
from collections import Counter
from pathlib import Path

RULE = "-" * 72


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--run", default="results/baseline")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--samples", type=int, default=2)
    args = p.parse_args(argv)

    run = Path(args.run)
    report = json.loads((run / "baseline_report.json").read_text(encoding="utf-8"))
    items = report["items"]
    raw = {}
    raw_path = run / "raw_generations.jsonl"
    if raw_path.exists():
        for line in raw_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                raw[r["id"]] = r

    failed = [i for i in items if not i["format_ok"]]
    print(f"{len(failed)} of {len(items)} generations failed to parse\n{RULE}")

    reasons = Counter(p for i in failed for p in (i["problems"] or ["(none recorded)"]))
    for reason, n in reasons.most_common():
        print(f"  {n:>3}  {reason}")

    by_lang = Counter(i["lang"] for i in failed)
    print(f"\nfailures by language: "
          f"{', '.join(f'{k}={v}' for k, v in sorted(by_lang.items()))}")

    if raw:
        print(f"\n{RULE}\noutput length vs the {args.max_new_tokens}-token cap")
        print(RULE)
        # Rough proxy: ~4 chars per token. Enough to see truncation clearly.
        cap_chars = args.max_new_tokens * 4
        ok_len, bad_len = [], []
        for i in items:
            text = raw.get(i["id"], {}).get("output", "")
            (ok_len if i["format_ok"] else bad_len).append(len(text))
        for label, lens in (("parsed ok", ok_len), ("failed", bad_len)):
            if lens:
                near = sum(1 for L in lens if L > 0.85 * cap_chars)
                print(f"  {label:<10} n={len(lens):<3} median={sorted(lens)[len(lens)//2]:>5} "
                      f"chars   max={max(lens):>5}   {near} within 15% of the cap")

        truncated = [i for i in failed
                     if "missing closing delimiter" in " ".join(i["problems"] or [])]
        if truncated:
            print(f"\n  {len(truncated)} failure(s) are a MISSING CLOSING DELIMITER.")
            print("  That is the signature of truncation: the model was still")
            print("  reasoning when generation stopped. Raise --max-new-tokens")
            print("  and re-run; these are not model errors.")

        print(f"\n{RULE}\nsample failed generations\n{RULE}")
        for i in failed[:args.samples]:
            text = raw.get(i["id"], {}).get("output", "")
            print(f"\n[{i['id']}] {i['problems']}")
            print(f"  ...{text[-300:]!r}")

    print(f"\n{RULE}")
    print("Correctness is a FLOOR while format failures remain: a generation")
    print("that does not parse is scored incorrect regardless of its content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
