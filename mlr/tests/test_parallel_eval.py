"""Multi-GPU evaluation must produce exactly what the sequential run produces.

A faster baseline that quietly reports different numbers is worse than a slow
one. These tests pin down the two places that could go wrong: how items are
divided, and how the pieces are put back together.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from mlr.evaluation import load_items, aggregate, score_item      # noqa: E402
from mlr.format_guard import GEMMA4_THINKING as FMT               # noqa: E402
from mlr.backends import MockBackend                              # noqa: E402
from mlr.baseline import run_baseline                             # noqa: E402
from run_eval_parallel import split_stratified, merge_reports     # noqa: E402

EVAL = ROOT / "data/eval/held_out_v1.jsonl"

THINK = {
    "en": "First I work through the steps and reach {a}.",
    "fr": "D'abord je travaille les étapes et j'obtiens {a}.",
    "sw": "Kwanza ninafanya hatua na kupata {a}.",
    "wo": "Bu njëkk damay def yëf yi te am {a}.",
}
ANSWER = {"en": "The answer is {a}.", "fr": "La réponse est {a}.",
          "sw": "Jibu ni {a}.", "wo": "Tontu li mooy {a}."}


def scripted(items):
    """One canned reply per question, varied so scoring branches are exercised."""
    script = {}
    for i, it in enumerate(items):
        lang = it.lang
        # Every third item reasons in English -- the collapse this project hunts.
        think_lang = "en" if (i % 3 == 1 and lang != "en") else lang
        script[it.question] = FMT.wrap(THINK[think_lang].format(a=it.gold),
                                       ANSWER[lang].format(a=it.gold))
    return script


class Splitting(unittest.TestCase):
    def setUp(self):
        self.rows = [json.loads(l) for l in
                     EVAL.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_every_shard_gets_every_language(self):
        for n in (2, 3, 4):
            shards = split_stratified(self.rows, n)
            for i, shard in enumerate(shards):
                langs = {r["lang"] for r in shard}
                self.assertEqual(langs, {"en", "fr", "sw", "wo"},
                                 f"n={n} shard {i} missing languages: {langs}")

    def test_naive_slicing_would_have_been_wrong(self):
        # Documents why split_stratified exists. The held-out file lists the
        # four languages adjacently, so rows[i::2] gives two languages only.
        naive = self.rows[0::2]
        self.assertNotEqual({r["lang"] for r in naive}, {"en", "fr", "sw", "wo"})

    def test_nothing_lost_or_duplicated(self):
        shards = split_stratified(self.rows, 2)
        ids = [r["id"] for s in shards for r in s]
        self.assertEqual(len(ids), len(self.rows))
        self.assertEqual(sorted(ids), sorted(r["id"] for r in self.rows))

    def test_shards_are_balanced_in_size(self):
        shards = split_stratified(self.rows, 2)
        self.assertLessEqual(abs(len(shards[0]) - len(shards[1])), 4)


class MergeMatchesSequential(unittest.TestCase):
    """The whole point: two GPUs must give the same answer as one."""

    def test_merged_report_equals_sequential_report(self):
        items = load_items(EVAL)
        script = scripted(items)

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            sequential = run_baseline(items, MockBackend(script=script),
                                      d / "seq" / "baseline", verbose=False)

            rows = [json.loads(l) for l in
                    EVAL.read_text(encoding="utf-8").splitlines() if l.strip()]
            shard_dirs = []
            for i, shard in enumerate(split_stratified(rows, 2)):
                ids = {r["id"] for r in shard}
                sub = [it for it in items if it.id in ids]
                sd = d / f"gpu{i}"
                run_baseline(sub, MockBackend(script=script), sd / "baseline",
                             verbose=False)
                shard_dirs.append(sd)

            merged = merge_reports(shard_dirs, "baseline", d / "merged")

        for lang in sequential["by_language"]:
            for metric in ("reasoning_correct", "reasoning_lang_ok",
                           "answer_lang_ok", "collapse_to_english",
                           "correct_and_in_language", "format_ok", "n"):
                self.assertAlmostEqual(
                    sequential["by_language"][lang][metric],
                    merged["by_language"][lang][metric], places=9,
                    msg=f"{lang}.{metric} differs between sequential and merged")
        self.assertEqual(sequential["overall"]["n"], merged["overall"]["n"])
        self.assertEqual(merged["parallel_shards"], 2)

    def test_merge_refuses_a_missing_shard(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                merge_reports([Path(d) / "gpu0"], "baseline", Path(d) / "merged")


if __name__ == "__main__":
    unittest.main(verbosity=2)
