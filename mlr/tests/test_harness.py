"""Prove the harness detects what it claims to detect.

These are not decoration. With the real weights unreachable, tests against a
scripted backend are the only evidence that a future baseline number means
what it says. Each test names the specific failure it is pinning down.
"""

import sys
import unittest
from pathlib import Path

# Make the suite runnable as plain `python3 -m unittest discover -s tests`
# with no PYTHONPATH ceremony.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mlr.format_guard import GEMMA4_THINKING as F, parse, check_translation
from mlr.langid import identify, code_switch_ratio
from mlr.evaluation import EvalItem, score_item, aggregate, answer_matches
from mlr.backends import MockBackend
from mlr.baseline import run_baseline

import tempfile


def wrap(thinking, answer):
    return F.wrap(thinking, answer)


class FormatGuard(unittest.TestCase):
    def test_parses_a_well_formed_response(self):
        p = parse(wrap("Kwanza, 3 x 12 = 36.", "Jibu ni 36."))
        self.assertTrue(p.ok, p.errors)
        self.assertEqual(p.thinking, "Kwanza, 3 x 12 = 36.")
        self.assertEqual(p.answer, "Jibu ni 36.")

    def test_missing_delimiter_is_caught(self):
        p = parse("Kwanza, 3 x 12 = 36. Jibu ni 36.")
        self.assertFalse(p.ok)
        self.assertIn("missing opening delimiter", p.errors)

    def test_duplicated_block_is_caught(self):
        p = parse(wrap("a", "b") + wrap("c", "d"))
        self.assertFalse(p.ok)

    def test_empty_reasoning_is_caught(self):
        self.assertFalse(parse(wrap("   ", "Jibu ni 36.")).ok)

    def test_translation_dropping_a_number_is_caught(self):
        src = wrap("First 3 x 12 = 36.", "The answer is 36.")
        bad = wrap("Kwanza 3 x 12 = 63.", "Jibu ni 63.")
        problems = check_translation(src, bad)
        self.assertTrue(any("number mismatch" in p for p in problems), problems)

    def test_translated_delimiter_is_caught(self):
        # MT translating the word inside the control token is the classic
        # silent break: it still looks like a think block to a human.
        src = wrap("First 3 x 12 = 36.", "The answer is 36.")
        broken = "<|channel>pensée\nD'abord 3 x 12 = 36.<channel|>La reponse est 36."
        self.assertTrue(check_translation(src, broken))

    def test_collapsed_reasoning_is_caught(self):
        src = wrap("First find the cost per bag, which is 3. "
                   "Then multiply by 4 bags to get 12. Check: 3 x 4 = 12.",
                   "The answer is 12.")
        stub = wrap("3 x 4 = 12", "Jibu 12.")
        self.assertTrue(any("shrank" in p for p in check_translation(
            src, stub, require_number_parity=False)))

    def test_clean_translation_passes(self):
        src = wrap("First, 3 x 12 = 36.", "The answer is 36.")
        good = wrap("Kwanza, 3 x 12 = 36.", "Jibu ni 36.")
        self.assertEqual(check_translation(src, good), [])


class LangId(unittest.TestCase):
    CASES = {
        "en": "First I need the total. Each bag is 3 and there are 4 bags, so the total is 12.",
        "fr": "D'abord je dois trouver le total. Chaque sac coûte 3 et il y a 4 sacs, donc le total est 12.",
        "sw": "Kwanza ninahitaji kupata jumla. Kila mfuko ni 3 na kuna mifuko 4, kwa hivyo jumla ni 12.",
        "wo": "Bu njëkk dama war a gis lépp. Benn mboot dafa jar 3, te am na 4 mboot, kon lépp mooy 12.",
    }

    def test_identifies_all_four(self):
        for want, text in self.CASES.items():
            self.assertEqual(identify(text).top, want, f"{want}: {text}")

    def test_wolof_with_french_numerals_is_still_wolof(self):
        t = ("Bu njëkk dama war a xam njëg li. Benn mboot dafa jar trois, "
             "te am na quatre mboot, kon lépp mooy douze.")
        self.assertEqual(identify(t).top, "wo")
        # ...but the switch is measurable, which is what the open policy
        # question about French-in-Wolof needs in order to be settled.
        self.assertGreater(code_switch_ratio(t, "wo", "fr"), 0.10)


class Scoring(unittest.TestCase):
    def item(self, lang="wo"):
        return EvalItem(id="t1", lang=lang, question="q", gold="36",
                        answer_type="numeric")

    def test_numeric_answer_is_language_independent(self):
        self.assertTrue(answer_matches("Jibu ni 36.", "36", "numeric"))
        self.assertTrue(answer_matches("La réponse est 36.", "36", "numeric"))
        self.assertTrue(answer_matches("Tontu li mooy 36.", "36", "numeric"))
        self.assertFalse(answer_matches("Jibu ni 63.", "36", "numeric"))

    def test_correct_and_in_language_passes(self):
        s = score_item(self.item(), wrap(
            "Bu njëkk dama war a xam lépp. 3 x 12 mooy 36. Kon lépp mooy 36.",
            "Tontu li mooy 36."))
        self.assertTrue(s.format_ok)
        self.assertTrue(s.correct)
        self.assertTrue(s.fully_ok, s)

    def test_reasoning_in_english_is_caught_even_when_answer_is_wolof(self):
        # Right answer, right answer-language, but the thinking collapsed.
        s = score_item(self.item(), wrap(
            "First I need the total. Each basket has 12 and there are 3 baskets, "
            "so the total is 36 and that is the answer.",
            "Tontu li mooy 36."))
        self.assertTrue(s.correct)
        self.assertFalse(s.reasoning_lang_ok)
        self.assertTrue(s.collapsed_to_english)
        self.assertFalse(s.fully_ok)

    def test_answer_collapsing_to_english_is_caught(self):
        s = score_item(self.item(), wrap(
            "Bu njëkk dama war a xam lépp. 3 x 12 mooy 36.",
            "The answer is 36 mangoes in total."))
        self.assertTrue(s.correct)
        self.assertTrue(s.reasoning_lang_ok)
        self.assertFalse(s.answer_lang_ok)
        self.assertTrue(s.collapsed_to_english)
        self.assertFalse(s.fully_ok)

    def test_broken_format_is_reported_separately_from_wrong_reasoning(self):
        s = score_item(self.item(), "3 x 12 = 36. Tontu li mooy 36.")
        self.assertFalse(s.format_ok)
        self.assertFalse(s.correct)
        self.assertTrue(s.problems)

    def test_aggregate_separates_the_two_questions(self):
        it = self.item()
        scores = [
            score_item(it, wrap("Bu njëkk 3 x 12 mooy 36. Kon lépp mooy 36.", "Tontu li mooy 36.")),
            score_item(it, wrap("First 3 x 12 is 36, so the total is 36 here.", "The answer is 36.")),
        ]
        rep = aggregate(scores)
        self.assertEqual(rep["overall"]["reasoning_correct"], 1.0)   # both right
        self.assertEqual(rep["overall"]["correct_and_in_language"], 0.5)  # one collapsed
        self.assertEqual(rep["overall"]["collapse_to_english"], 0.5)


class EndToEnd(unittest.TestCase):
    def test_baseline_runs_and_reports(self):
        items = [
            EvalItem(id="a-sw", lang="sw", question="Vikapu 3, maembe 12 kila kimoja?",
                     gold="36", answer_type="numeric"),
            EvalItem(id="a-wo", lang="wo", question="3 pañe, 12 mango ci benn?",
                     gold="36", answer_type="numeric"),
        ]
        backend = MockBackend(script={
            "Vikapu": wrap("Kwanza, vikapu ni 3 na kila kimoja kina maembe 12. "
                           "Kwa hivyo 3 x 12 = 36.", "Jibu ni 36."),
            "pañe": wrap("First, there are 3 baskets with 12 mangoes each, "
                         "so 3 times 12 is 36.", "The answer is 36."),
        })
        with tempfile.TemporaryDirectory() as d:
            rep = run_baseline(items, backend, d, verbose=False)
        self.assertEqual(rep["overall"]["n"], 2)
        self.assertEqual(rep["overall"]["reasoning_correct"], 1.0)
        self.assertEqual(rep["by_language"]["sw"]["correct_and_in_language"], 1.0)
        self.assertEqual(rep["by_language"]["wo"]["correct_and_in_language"], 0.0)
        self.assertEqual(rep["by_language"]["wo"]["collapse_to_english"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
