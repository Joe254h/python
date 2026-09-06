"""Protect the reasoning format across translation.

Protocol item 3: the reasoning structure (think block, then final answer) must
survive translation intact. Machine translation routinely mangles control
tokens -- it will happily translate the literal word "thought" inside a
delimiter, re-order the block, or drop it entirely. When that happens the
fine-tune learns nothing useful, and the damage is invisible in a spot check.

Every delimiter lives in ThinkingFormat so there is exactly one place to
correct if the spelling below turns out to be wrong.

WARNING -- UNVERIFIED CONSTANT:
    GEMMA4_THINKING was taken from secondary sources (docs summaries and
    community write-ups), not from the tokenizer itself, because
    huggingface.co and ai.google.dev are both blocked by this environment's
    egress policy. Before any training run, call
    ThinkingFormat.resolve_from_tokenizer() to confirm the spelling against
    the real tokenizer. Do not trust these strings until that passes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence


class FormatError(Exception):
    """Raised when a record cannot be parsed at all."""


@dataclass(frozen=True)
class ThinkingFormat:
    """Delimiters that wrap a model's reasoning block."""

    open_token: str
    close_token: str
    name: str = "unnamed"

    def wrap(self, thinking: str, answer: str) -> str:
        """Render a (thinking, answer) pair into a single formatted string."""
        return f"{self.open_token}{thinking}{self.close_token}{answer}"

    def resolve_from_tokenizer(self, tokenizer) -> "ThinkingFormat":
        """Confirm these delimiters exist in a real tokenizer's vocabulary.

        Raises FormatError if a delimiter is not a known piece of the
        vocabulary, which means the constants below are stale and every
        downstream guarantee in this module is void.
        """
        vocab = set(getattr(tokenizer, "get_vocab", dict)())
        missing = [
            tok
            for tok in (self.open_token, self.close_token)
            if tok not in vocab and len(tokenizer.tokenize(tok)) > 1
        ]
        if missing:
            raise FormatError(
                f"delimiters {missing!r} are not atomic tokens for this "
                f"tokenizer; update ThinkingFormat before training"
            )
        return self


# Gemma 4 emits its reasoning on a named "thought" channel. See the warning in
# the module docstring: verify before relying on this.
GEMMA4_THINKING = ThinkingFormat(
    open_token="<|channel>thought\n",
    close_token="<channel|>",
    name="gemma4",
)

# The upstream Multilingual-Thinking rows are gpt-oss Harmony records, which
# keep reasoning in a separate `thinking` field rather than inline delimiters.
# Conversion is handled in harmony_to_gemma.py; this entry exists so the guard
# can also validate text that already uses the common <think> convention.
GENERIC_THINK = ThinkingFormat(
    open_token="<think>",
    close_token="</think>",
    name="generic",
)


@dataclass
class Parsed:
    """Result of splitting a formatted response into its two parts."""

    thinking: str
    answer: str
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


def parse(text: str, fmt: ThinkingFormat = GEMMA4_THINKING) -> Parsed:
    """Split `text` into its reasoning block and its final answer.

    Never raises for malformed input -- returns a Parsed with ok=False and a
    list of what is wrong, so a whole dataset can be screened in one pass.
    """
    errors: list[str] = []
    n_open = text.count(fmt.open_token)
    n_close = text.count(fmt.close_token)

    if n_open == 0:
        errors.append("missing opening delimiter")
    if n_close == 0:
        errors.append("missing closing delimiter")
    if n_open > 1:
        errors.append(f"{n_open} opening delimiters, expected exactly 1")
    if n_close > 1:
        errors.append(f"{n_close} closing delimiters, expected exactly 1")
    if errors:
        return Parsed(thinking="", answer="", ok=False, errors=errors)

    start = text.index(fmt.open_token)
    end = text.index(fmt.close_token)
    if end < start:
        return Parsed("", "", False, ["closing delimiter precedes opening delimiter"])

    thinking = text[start + len(fmt.open_token) : end]
    answer = text[end + len(fmt.close_token) :]

    if not thinking.strip():
        errors.append("empty reasoning block")
    if not answer.strip():
        errors.append("empty final answer")
    if text[:start].strip():
        errors.append("text leaks before the reasoning block")

    return Parsed(thinking.strip(), answer.strip(), ok=not errors, errors=errors)


# Digits, and separately number-words, both matter: a trace that says "45" in
# English and "54" in Swahili is silently wrong in a way no format check sees.
_DIGITS = re.compile(r"\d+(?:[.,]\d+)*")


def _numbers(text: str) -> list[str]:
    """Extract digit-strings, normalised so 1,000 and 1000 compare equal."""
    out = []
    for match in _DIGITS.findall(text):
        out.append(match.replace(",", "").replace(".", ""))
    return sorted(out)


def check_translation(
    source: str,
    target: str,
    fmt: ThinkingFormat = GEMMA4_THINKING,
    *,
    require_number_parity: bool = True,
) -> list[str]:
    """Return the list of ways `target` fails to preserve `source`'s format.

    An empty list means the translation is structurally safe to train on. This
    checks structure and numeric fidelity only -- it says nothing about whether
    the translation is any good, which is what native validation is for.
    """
    problems: list[str] = []

    src = parse(source, fmt)
    tgt = parse(target, fmt)

    if not src.ok:
        problems.extend(f"source: {e}" for e in src.errors)
    if not tgt.ok:
        problems.extend(f"target: {e}" for e in tgt.errors)
    if problems:
        return problems

    # A translated delimiter is the classic silent failure: the block still
    # looks present to a human skimming, but the token no longer matches.
    for stray in ("<|channel", "channel|>", "<think", "</think", "thought\n"):
        leaked = tgt.thinking.count(stray) + tgt.answer.count(stray)
        if leaked:
            problems.append(f"target: delimiter fragment {stray!r} leaked into content")

    if require_number_parity:
        src_nums, tgt_nums = _numbers(source), _numbers(target)
        if src_nums != tgt_nums:
            problems.append(
                f"number mismatch: source has {src_nums or '[]'}, "
                f"target has {tgt_nums or '[]'}"
            )

    # A reasoning trace that collapses to a fraction of its source length has
    # usually lost steps rather than been elegantly compressed.
    if src.thinking and len(tgt.thinking) < 0.4 * len(src.thinking):
        problems.append(
            f"reasoning block shrank to {len(tgt.thinking)}/{len(src.thinking)} "
            f"chars; steps were probably dropped"
        )

    return problems


def screen(records: Iterable[dict], languages: Sequence[str], source_lang: str = "en",
           fmt: ThinkingFormat = GEMMA4_THINKING) -> dict[str, list[str]]:
    """Screen a whole dataset. Returns {record_id: [problems]} for failures only."""
    failures: dict[str, list[str]] = {}
    for rec in records:
        rid = str(rec.get("id", "<no id>"))
        src = rec["translations"][source_lang]
        rendered_src = fmt.wrap(src["thinking"], src["answer"])
        for lang in languages:
            if lang == source_lang or lang not in rec["translations"]:
                continue
            tgt = rec["translations"][lang]
            rendered = fmt.wrap(tgt["thinking"], tgt["answer"])
            issues = check_translation(rendered_src, rendered, fmt)
            if issues:
                failures.setdefault(rid, []).extend(f"[{lang}] {i}" for i in issues)
    return failures
