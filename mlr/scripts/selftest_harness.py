#!/usr/bin/env python3
"""Run the full baseline pipeline on synthetic outputs.

This exists to show what the baseline report will look like, and to prove the
pipeline works end to end on the real 48-item held-out set, WITHOUT a model.

The numbers it produces are meaningless. They come from a scripted pattern, not
from Gemma 4. The output file says so on every read.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mlr.evaluation import load_items                    # noqa: E402
from mlr.format_guard import GEMMA4_THINKING as FMT      # noqa: E402
from mlr.baseline import run_baseline                    # noqa: E402

# Deliberately varied synthetic responses, so every branch of the scoring code
# is exercised: in-language and correct, collapsed reasoning, collapsed answer,
# wrong arithmetic, and a broken think block.
THINK = {
    "en": "First I work through the steps carefully, and the result comes to {a}.",
    "fr": "D'abord je travaille les étapes avec soin, et le résultat donne {a}.",
    "sw": "Kwanza ninafanya hatua kwa makini, na jibu linakuwa {a}.",
    "wo": "Bu njëkk dama war a xool yëf yi ci teey, kon njariñ li mooy {a}.",
}
ANSWER = {
    "en": "The answer is {a}.", "fr": "La réponse est {a}.",
    "sw": "Jibu ni {a}.", "wo": "Tontu li mooy {a}.",
}


def synthetic(item, i):
    a = item.gold
    mode = i % 5
    if mode == 0:                                    # clean and correct
        return FMT.wrap(THINK[item.lang].format(a=a), ANSWER[item.lang].format(a=a))
    if mode == 1 and item.lang != "en":              # reasoning collapsed to English
        return FMT.wrap(THINK["en"].format(a=a), ANSWER[item.lang].format(a=a))
    if mode == 2 and item.lang != "en":              # answer collapsed to English
        return FMT.wrap(THINK[item.lang].format(a=a), ANSWER["en"].format(a=a))
    if mode == 3:                                    # in-language but wrong
        wrong = a[::-1] if a.isdigit() else "Bineta"
        return FMT.wrap(THINK[item.lang].format(a=wrong), ANSWER[item.lang].format(a=wrong))
    return THINK[item.lang].format(a=a) + " " + ANSWER[item.lang].format(a=a)  # no think block


class ScriptedBackend:
    name = "synthetic-selftest"

    def __init__(self, items):
        self.replies = {it.question: synthetic(it, i) for i, it in enumerate(items)}

    def generate(self, system, user, max_new_tokens=512):
        return self.replies[user]


def main() -> None:
    items = load_items(ROOT / "data/eval/held_out_v1.jsonl")
    out = ROOT / "results/selftest"
    report = run_baseline(items, ScriptedBackend(items), out, verbose=False)

    rule = "=" * 72
    banner = "\n".join([
        rule,
        "HARNESS SELF-TEST -- THESE NUMBERS ARE NOT A BASELINE",
        rule,
        "",
        "Generated from a scripted pattern, not from Gemma 4. Gemma 4 has never",
        "been run in this repository -- huggingface.co is blocked by egress",
        "policy (see docs/BLOCKERS.md). This file exists only to show the shape",
        "of the report and to prove the pipeline runs on all 48 held-out items.",
        "",
        "Do not cite any figure below.",
        rule,
        "",
        "",
    ])
    table = (out / "baseline_table.txt").read_text(encoding="utf-8")
    dest = ROOT / "results/HARNESS_SELFTEST_NOT_A_BASELINE.txt"
    dest.write_text(banner + table + "\n", encoding="utf-8")
    print(banner + table)
    print(f"\nscored {report['overall']['n']} items across "
          f"{len(report['by_language'])} languages -- pipeline works end to end")


if __name__ == "__main__":
    main()
