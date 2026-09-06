"""Evaluation, defined before training rather than after.

Protocol item 5. Two things are measured, and they are never collapsed into
one number:

  1. Does it reason correctly?   -> `correct`, judged on the final answer only.
  2. Does it answer in the language it was asked in?  -> `answer_lang_ok`,
     and separately `reasoning_lang_ok`.

Splitting language fidelity in two is the point. The failure this project is
built to catch has two distinct shapes, and a single score hides both:

  * reasons in English, answers in Wolof  -- looks fine to a user skimming the
    answer, but the thinking has collapsed and the model is not actually
    reasoning in the target language;
  * reasons in Wolof, answers in English  -- the classic low-resource collapse,
    where the model loses the language exactly when it matters.

A third measurement, `format_ok`, is reported on its own and never silently
folded into correctness. If a fine-tune breaks the think-block format, the
correctness number will crater, and without a separate format channel that
looks like a reasoning regression when it is really a formatting bug.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, Sequence

from .format_guard import ThinkingFormat, GEMMA4_THINKING, parse
from .langid import identify, code_switch_ratio

# How much French inside a Wolof response still counts as Wolof.
#
# OPEN QUESTION -- this threshold is not yet decided by evidence. Wolof
# speakers ordinarily count and do arithmetic in French, so some French in a
# Wolof reasoning trace is natural speech, not collapse. Set too low, the
# metric punishes correct Wolof; set too high, it lets real collapse through.
# Pending native-speaker guidance this is a placeholder, and every result
# computed with it must be reported alongside the value used.
WOLOF_FRENCH_TOLERANCE = 0.40

_ANSWER_HINTS = re.compile(
    r"(?:answer|réponse|reponse|jibu|tontu)\s*[:=]?\s*", re.IGNORECASE
)
_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


@dataclass
class EvalItem:
    """One held-out reasoning problem, in one language."""

    id: str
    lang: str
    question: str
    gold: str
    answer_type: str = "exact"   # exact | numeric | set
    domain: str = "general"
    system: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "EvalItem":
        return cls(**{k: v for k, v in d.items() if k in cls.__annotations__})


@dataclass
class ItemScore:
    """Everything measured about one prediction, kept separable."""

    id: str
    lang: str
    format_ok: bool
    correct: bool
    reasoning_lang: str
    answer_lang: str
    reasoning_lang_ok: bool
    answer_lang_ok: bool
    collapsed_to_english: bool
    french_share: float = 0.0
    predicted: str = ""
    problems: list[str] = field(default_factory=list)

    @property
    def fully_ok(self) -> bool:
        """The headline condition: right answer, in the right language, both ways."""
        return (
            self.format_ok
            and self.correct
            and self.reasoning_lang_ok
            and self.answer_lang_ok
        )


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().strip()
    text = _ANSWER_HINTS.sub("", text)
    text = re.sub(r"[\s ]+", " ", text)
    return text.strip(" .!?:;،,")


def _numbers_in(text: str) -> list[float]:
    out = []
    for m in _NUM.findall(text.replace(" ", "").replace(" ", "")):
        try:
            out.append(float(m.replace(",", ".")))
        except ValueError:
            pass
    return out


def answer_matches(pred: str, gold: str, answer_type: str = "exact") -> bool:
    """Judge the final answer only. Reasoning is free-form and never scored here."""
    p, g = _normalise(pred), _normalise(gold)
    if answer_type == "numeric":
        gold_nums = _numbers_in(g)
        pred_nums = _numbers_in(p)
        if not gold_nums:
            return p == g
        if not pred_nums:
            return False
        # The answer is the last number stated: models restate the working
        # before committing, and the commitment is what we grade.
        return abs(pred_nums[-1] - gold_nums[-1]) < 1e-6
    if answer_type == "set":
        split = lambda s: {x.strip() for x in re.split(r"[,;/]| and | et | na | ak ", s) if x.strip()}
        return split(p) == split(g)
    return p == g or g in p


def language_ok(text: str, want: str) -> tuple[bool, str, float]:
    """Is `text` in language `want`? Returns (ok, detected, french_share)."""
    res = identify(text)
    french_share = res.mixture.get("fr", 0.0) if res.mixture else 0.0

    if not text.strip():
        return False, "empty", 0.0

    if want == "wo":
        # Wolof with French numerals is still Wolof. Judge it on the wo/fr
        # balance rather than on the raw argmax, which French numerals can flip.
        switch = code_switch_ratio(text, "wo", "fr")
        if res.top in ("wo", "fr"):
            return switch <= WOLOF_FRENCH_TOLERANCE, res.top, switch
        return False, res.top, switch

    return res.top == want, res.top, french_share


def score_item(
    item: EvalItem,
    raw_output: str,
    fmt: ThinkingFormat = GEMMA4_THINKING,
) -> ItemScore:
    """Score one prediction against one held-out item."""
    parsed = parse(raw_output, fmt)
    problems = list(parsed.errors)

    if not parsed.ok:
        # Without a parse there is no answer to grade and no blocks to language-ID.
        # Recorded as a format failure, not silently as a wrong answer.
        return ItemScore(
            id=item.id, lang=item.lang, format_ok=False, correct=False,
            reasoning_lang="n/a", answer_lang="n/a",
            reasoning_lang_ok=False, answer_lang_ok=False,
            collapsed_to_english=False, predicted=raw_output[:200],
            problems=problems,
        )

    correct = answer_matches(parsed.answer, item.gold, item.answer_type)
    r_ok, r_lang, _ = language_ok(parsed.thinking, item.lang)
    a_ok, a_lang, fr_share = language_ok(parsed.answer, item.lang)

    collapsed = item.lang != "en" and (r_lang == "en" or a_lang == "en")

    return ItemScore(
        id=item.id, lang=item.lang, format_ok=True, correct=correct,
        reasoning_lang=r_lang, answer_lang=a_lang,
        reasoning_lang_ok=r_ok, answer_lang_ok=a_ok,
        collapsed_to_english=collapsed, french_share=fr_share,
        predicted=parsed.answer[:200], problems=problems,
    )


def aggregate(scores: Sequence[ItemScore]) -> dict:
    """Per-language and overall rollup. Every rate is reported separately."""

    def rates(subset: Sequence[ItemScore]) -> dict:
        n = len(subset)
        if n == 0:
            return {"n": 0}
        return {
            "n": n,
            "format_ok": sum(s.format_ok for s in subset) / n,
            "reasoning_correct": sum(s.correct for s in subset) / n,
            "reasoning_lang_ok": sum(s.reasoning_lang_ok for s in subset) / n,
            "answer_lang_ok": sum(s.answer_lang_ok for s in subset) / n,
            "collapse_to_english": sum(s.collapsed_to_english for s in subset) / n,
            "correct_and_in_language": sum(s.fully_ok for s in subset) / n,
        }

    langs = sorted({s.lang for s in scores})
    return {
        "overall": rates(scores),
        "by_language": {L: rates([s for s in scores if s.lang == L]) for L in langs},
        "wolof_french_tolerance": WOLOF_FRENCH_TOLERANCE,
    }


def load_items(path: str | Path) -> list[EvalItem]:
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            items.append(EvalItem.from_dict(json.loads(line)))
    return items


def write_report(scores: Sequence[ItemScore], path: str | Path) -> dict:
    report = aggregate(scores)
    payload = {"summary": report, "items": [asdict(s) for s in scores]}
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def format_table(report: dict) -> str:
    """Human-readable rollup for the terminal."""
    cols = [
        ("format", "format_ok"),
        ("correct", "reasoning_correct"),
        ("think-lang", "reasoning_lang_ok"),
        ("ans-lang", "answer_lang_ok"),
        ("collapse-EN", "collapse_to_english"),
        ("BOTH", "correct_and_in_language"),
    ]
    head = f"{'lang':>6} {'n':>4} " + " ".join(f"{c[0]:>11}" for c in cols)
    lines = [head, "-" * len(head)]
    for lang, r in report["by_language"].items():
        if not r.get("n"):
            continue
        cells = " ".join(f"{r[k]:>10.0%} " for _, k in cols)
        lines.append(f"{lang:>6} {r['n']:>4} {cells}")
    o = report["overall"]
    if o.get("n"):
        cells = " ".join(f"{o[k]:>10.0%} " for _, k in cols)
        lines.append("-" * len(head))
        lines.append(f"{'ALL':>6} {o['n']:>4} {cells}")
    lines.append(f"\nWolof French-tolerance in force: {report['wolof_french_tolerance']:.0%}")
    return "\n".join(lines)
