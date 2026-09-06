"""Training-data assembly, with the verification protocol enforced in code.

Protocol item 2 says nothing unverified ships. A rule that lives only in a
document gets forgotten at 2am before a deadline, so it lives here instead:
`load_training_rows` refuses to hand back rows that no human has signed off,
and the caller has to pass `allow_unverified=True` and say so out loud to get
them. That flag is recorded in the model card, so a model trained on
unverified Wolof can always be identified after the fact.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .format_guard import GEMMA4_THINKING, ThinkingFormat, check_translation

LANGUAGES = ("en", "fr", "sw", "wo")


class UnverifiedDataError(RuntimeError):
    """Raised when unverified rows would silently enter a training run."""


@dataclass
class Corpus:
    """A prepared training corpus plus everything needed to describe it later."""

    train: list[dict]
    val: list[dict]
    composition: dict[str, int]
    unverified_langs: list[str]
    allow_unverified: bool
    fingerprint: str
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"train {len(self.train)}  val {len(self.val)}",
            "by language: " + ", ".join(
                f"{k}={v}" for k, v in sorted(self.composition.items())),
            f"fingerprint: {self.fingerprint}",
        ]
        if self.unverified_langs:
            state = "ALLOWED BY OVERRIDE" if self.allow_unverified else "excluded"
            lines.append(f"unverified languages ({state}): "
                         f"{', '.join(self.unverified_langs)}")
        lines.extend(self.notes)
        return "\n".join(lines)


def load_rows(path: str | Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def fingerprint(rows: Sequence[dict]) -> str:
    """Stable hash of the training content, so a model card can name its data."""
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: r["id"]):
        h.update(r["id"].encode())
        h.update(r["rendered"].encode())
    return h.hexdigest()[:16]


def render_for_training(row: dict, fmt: ThinkingFormat = GEMMA4_THINKING) -> dict:
    """Turn a stored row into the fields a chat-template trainer wants."""
    msgs = row["messages"]
    system = next((m["content"] for m in msgs if m["role"] == "system"), "")
    user = next(m["content"] for m in msgs if m["role"] == "user")
    assistant = next(m for m in msgs if m["role"] == "assistant")
    return {
        "id": row["id"],
        "lang": row["lang"],
        "system": system,
        "user": user,
        "thinking": assistant["thinking"],
        "answer": assistant["content"],
        "target": fmt.wrap(assistant["thinking"], assistant["content"]),
    }


def load_training_rows(
    path: str | Path,
    *,
    languages: Iterable[str] = LANGUAGES,
    allow_unverified: bool = False,
    val_fraction: float = 0.2,
    seed: int = 0,
    fmt: ThinkingFormat = GEMMA4_THINKING,
) -> Corpus:
    """Load, screen and split the training data.

    Raises UnverifiedDataError if unverified rows are present and the caller
    has not explicitly opted in. Rows whose think-block format is broken are
    always dropped: training on them teaches the model to emit output the
    parser cannot read, which is worse than having fewer examples.
    """
    languages = tuple(languages)
    rows = [r for r in load_rows(path) if r["lang"] in languages]
    notes: list[str] = []

    unverified = sorted({r["lang"] for r in rows if not r.get("human_verified")})

    if unverified and not allow_unverified:
        raise UnverifiedDataError(
            f"rows in {unverified} have human_verified=false. Native validation "
            f"is required before training on them (protocol item 2). To proceed "
            f"anyway for a pipeline smoke-test, pass allow_unverified=True -- the "
            f"choice is recorded in the model card and such a run must not be "
            f"reported as a result."
        )
    if unverified and allow_unverified:
        notes.append(
            f"WARNING: training on UNVERIFIED {', '.join(unverified)}. "
            f"This run is a pipeline test, not a result."
        )

    # Drop anything whose format does not survive; never train on a broken block.
    kept, dropped = [], []
    by_sample: dict[str, dict] = {}
    for r in rows:
        by_sample.setdefault(r["sample_id"], {})[r["lang"]] = r

    for r in rows:
        src = by_sample.get(r["sample_id"], {}).get("en")
        if src is not None and r["lang"] != "en":
            if check_translation(src["rendered"], r["rendered"], fmt):
                dropped.append(r["id"])
                continue
        kept.append(r)
    if dropped:
        notes.append(f"dropped {len(dropped)} rows failing the format guard: "
                     f"{', '.join(dropped[:5])}{'...' if len(dropped) > 5 else ''}")

    # Split by sample_id, not by row: the same problem in four languages must
    # not straddle the train/val boundary or validation leaks.
    sample_ids = sorted({r["sample_id"] for r in kept})
    rng = random.Random(seed)
    rng.shuffle(sample_ids)
    n_val = max(1, round(len(sample_ids) * val_fraction)) if sample_ids else 0
    val_ids = set(sample_ids[:n_val])

    train = [render_for_training(r, fmt) for r in kept if r["sample_id"] not in val_ids]
    val = [render_for_training(r, fmt) for r in kept if r["sample_id"] in val_ids]
    rng.shuffle(train)

    return Corpus(
        train=train,
        val=val,
        composition=dict(Counter(r["lang"] for r in kept)),
        unverified_langs=unverified,
        allow_unverified=allow_unverified,
        fingerprint=fingerprint(kept),
        notes=notes,
    )


def to_chat_messages(row: dict) -> list[dict]:
    """Chat-format messages for `apply_chat_template`."""
    msgs = []
    if row["system"]:
        msgs.append({"role": "system", "content": row["system"]})
    msgs.append({"role": "user", "content": row["user"]})
    msgs.append({"role": "assistant", "content": row["target"]})
    return msgs
