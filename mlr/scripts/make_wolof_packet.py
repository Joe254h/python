#!/usr/bin/env python3
"""Emit the Wolof native-review packet.

Nothing Wolof in this project ships without native validation. A reviewer
handed 32 items and told "check everything" works slowly and misses things, so
this packet does three things instead: it puts the English source directly
beside each Wolof draft, it names the specific choice I am unsure about on
each item, and it puts the one policy decision that blocks the rest at the top.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data" / "sample20"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from records import SAMPLES                        # noqa: E402
from mlr.langid import code_switch_ratio           # noqa: E402

EVAL = Path("data/eval/held_out_v1.jsonl")
OUT = Path("docs/WOLOF_REVIEW_PACKET.md")

HEADER = """# Wolof native-review packet

**Status: nothing here is validated. None of it may be trained on or evaluated
against until a native Wolof speaker has been through it.**

Everything below was produced by a language model (me). It is drafted in the
official Senegalese orthography (`ë`, `ñ`, `ŋ`, `à`), but the orthography, the
word choices and the register all need a native speaker's judgement.

## What we need from you

For each item, three questions:

1. **Is it correct?** Does the Wolof say what the English says? Errors in the
   reasoning steps matter more than errors in the final sentence -- the whole
   point of this dataset is the reasoning.
2. **Is it natural?** Would a Wolof speaker explaining this to a friend
   actually put it this way, or does it read as translated French?
3. **Is the flagged choice right?** Each item lists the specific words I am
   unsure about. Those are where I would put your time first.

Corrections can be written straight into the "correction" line. If an item is
beyond repair, mark it `REJECT` -- a rejected item is far more useful to us
than a patched-up one, and the protocol here is quality over quantity.

---

## Decision 1 (blocking): how much French belongs in Wolof reasoning?

This one decision changes both the dataset and the way the model is scored, so
it needs settling before the rest of the review is worth doing.

Wolof speakers routinely count and do arithmetic in French. Wolof has its own
numerals (`benn, ñaar, ñett, ñeent, juróom, fukk`, and the quinary forms above
five), but in ordinary speech -- especially prices, measurements and mental
arithmetic -- French numerals are extremely common.

That leaves three options for the reasoning traces:

| option | what a trace looks like | risk |
|---|---|---|
| **A. Natural** | Wolof grammar, French numerals and technical loanwords wherever a speaker would use them | The model learns real Wolof, but "answers in Wolof" gets harder to measure automatically |
| **B. Purist** | Wolof numerals and Wolof coinages throughout | Clean to measure, but may teach a register no one actually speaks |
| **C. Split** | Natural in the reasoning block, Wolof-dominant in the final answer | Closest to real usage, but the two halves are trained on inconsistent conventions |

This is not only a linguistic question, it decides an evaluation threshold.
The evaluation flags a Wolof response as "collapsed into another language"
when the French share passes `WOLOF_FRENCH_TOLERANCE` (currently a placeholder
of 40%). Choose A and the threshold has to be loose, which risks letting real
collapse pass as natural code-switching. Choose B and it can be tight, but the
metric will punish Wolof that is perfectly normal.

**What we need:** which option, and roughly what share of French in a Wolof
reasoning trace should count as still-Wolof rather than a collapse.

---

## Decision 2: orthography

These drafts use official Senegalese orthography. Much Wolof written online
uses French-influenced spelling instead (`gni` for `ñu`, `kh` for `x`). Which
convention should the model be trained to produce? If learners and everyday
readers are the audience, the answer may not be the official one.

---
"""

FOOTER = """
## Sign-off

| reviewer | date | items reviewed | items rejected |
|---|---|---|---|
|  |  |  |  |

Once signed off, set `human_verified: true` for the reviewed rows in
`data/sample20/sample20.jsonl` and record the reviewer in
`data/sample20/PROVENANCE.md`. Until then every row stays `human_verified:
false`, and no Wolof number computed from this data should be reported as
final.
"""


def main() -> None:
    lines = [HEADER, "## Part 1 -- training sample (20 items)", ""]

    for i, s in enumerate(SAMPLES, 1):
        wo_think = s["thinking"]["wo"]
        fr_share = code_switch_ratio(wo_think, "wo", "fr")
        lines += [
            f"### {i}. `{s['id']}`  ({s['domain']})",
            "",
            f"**English source question:** {s['question']['en']}",
            "",
            f"**Wolof question:** {s['question']['wo']}",
            "",
            f"**English reasoning:** {s['thinking']['en']}",
            "",
            f"**Wolof reasoning:** {wo_think}",
            "",
            f"**Wolof answer:** {s['answer']['wo']}",
            "",
            f"*Measured French share of the reasoning: {fr_share:.0%}*",
            "",
            "**Specific points I am unsure about:**",
        ]
        for note in s.get("wo_review", []) or ["(none flagged)"]:
            lines.append(f"- {note}")
        lines += [
            "",
            "- [ ] correct  - [ ] natural  - [ ] REJECT",
            "",
            "**correction:**",
            "",
            "---",
            "",
        ]

    lines += ["## Part 2 -- held-out evaluation questions (12 items)", "",
              "These are the questions the model is *scored* on. A mistranslation",
              "here produces a wrong score, which is worse than no score, so they",
              "need the same scrutiny as the training data.", ""]

    if EVAL.exists():
        wo_items = [json.loads(l) for l in EVAL.read_text(encoding="utf-8").splitlines()
                    if l.strip() and json.loads(l)["lang"] == "wo"]
        by_id = {json.loads(l)["id"]: json.loads(l)
                 for l in EVAL.read_text(encoding="utf-8").splitlines() if l.strip()}
        for it in wo_items:
            en = by_id.get(it["id"].replace("-wo", "-en"), {}).get("question", "")
            lines += [
                f"### `{it['id']}`",
                "",
                f"**English:** {en}",
                "",
                f"**Wolof:** {it['question']}",
                "",
                f"*(expected answer: {it['gold']})*",
                "",
                "- [ ] correct  - [ ] natural  - [ ] REJECT",
                "",
                "**correction:**",
                "",
                "---",
                "",
            ]

    lines.append(FOOTER)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    n_flags = sum(len(s.get("wo_review", [])) for s in SAMPLES)
    print(f"wrote {OUT}  ({len(SAMPLES)} training items + 12 eval items, "
          f"{n_flags} specific flagged points)")


if __name__ == "__main__":
    main()
