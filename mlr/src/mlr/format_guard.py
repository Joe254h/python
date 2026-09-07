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
    """Delimiters that wrap a model's reasoning block.

    `open_emitted_by_template` is the subtle one, and getting it wrong is
    silent. Many thinking-model chat templates emit the OPENING marker as part
    of the generation prompt, so the model's own output begins *inside* the
    reasoning block and contains only `thinking + close + answer`. When that is
    true:

      * generated text has no opening delimiter, and parsing must not demand
        one -- otherwise every single generation is scored as a format failure;
      * a training target must not carry one either, or the model learns to
        emit a second opening marker on top of the template's.

    Do not hand-set this. `detect_thinking_format` works it out from the
    tokenizer, which is the only authority on it.
    """

    open_token: str
    close_token: str
    name: str = "unnamed"
    open_emitted_by_template: bool = False

    def wrap(self, thinking: str, answer: str) -> str:
        """Canonical full form. Used for cross-language format comparison,
        where all that matters is that every language is rendered alike."""
        return f"{self.open_token}{thinking}{self.close_token}{answer}"

    def training_target(self, thinking: str, answer: str) -> str:
        """What the model must actually learn to emit after the prompt.

        This is deliberately not `wrap`: if the template already opened the
        block, repeating the marker here trains a duplicate.
        """
        if self.open_emitted_by_template:
            return f"{thinking}{self.close_token}{answer}"
        return self.wrap(thinking, answer)

    def resolve_from_tokenizer(self, tokenizer) -> "ThinkingFormat":
        """Return the format this tokenizer actually uses.

        Detection wins over the configured constants, because the tokenizer is
        the authority and the constants are a guess. Raises FormatError only
        when detection fails AND the configured delimiters appear nowhere in
        the chat template -- at that point we genuinely do not know the format
        and training would produce unparseable output.
        """
        detected = detect_thinking_format(tokenizer, name=self.name)
        if detected is not None:
            return detected

        template = _chat_template_source(tokenizer)
        if template and self.close_token in template:
            # Close marker confirmed in the template but the open/prompt
            # relationship could not be established; keep the configured pair.
            return self

        raise FormatError(
            f"could not determine the thinking format for this tokenizer, and "
            f"the configured close delimiter {self.close_token!r} does not "
            f"appear in its chat template. Run "
            f"`python scripts/inspect_chat_template.py --model <id>` and set "
            f"ThinkingFormat from what it prints."
        )


def _chat_template_source(tokenizer) -> str:
    """The chat template as a string, however this tokenizer version exposes it."""
    template = getattr(tokenizer, "chat_template", None)
    if isinstance(template, dict):                     # some versions key by name
        template = template.get("default") or next(iter(template.values()), "")
    return template if isinstance(template, str) else ""


_THINK_WORDS = ("thought", "think", "channel", "analysis", "reasoning")

# Matches a Jinja concatenation of the form  'OPEN' + var + 'CLOSE'  which is
# how a chat template emits a reasoning block around its content. Gemma 4's
# template contains exactly this:
#     {{- '<|channel>thought\n' + thinking_text + '\n<channel|>' -}}
_JINJA_PAIR = re.compile(
    r"'((?:[^'\\]|\\.)*)'\s*\+\s*[\w.\[\]'()]+\s*\+\s*'((?:[^'\\]|\\.)*)'"
)


def _unescape(literal: str) -> str:
    """Turn a Jinja source literal's backslash escapes into real characters."""
    try:
        return literal.encode("utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        return literal


def _pair_from_template(template: str) -> "tuple[str, str] | None":
    """Read the delimiter pair out of the chat template's own source."""
    for match in _JINJA_PAIR.finditer(template or ""):
        open_lit, close_lit = match.group(1), match.group(2)
        if not any(w in (open_lit + close_lit).lower() for w in _THINK_WORDS):
            continue
        open_tok = _unescape(open_lit)
        # The template writes a newline before the closing marker. Drop it: the
        # marker itself is what has to match, and requiring the newline would
        # fail on any generation that omits it.
        close_tok = _unescape(close_lit).lstrip("\n")
        if open_tok and close_tok:
            return open_tok, close_tok
    return None


def _render(tokenizer, **kwargs) -> str | None:
    probe = [{"role": "user", "content": "__PROBE__"}]
    try:
        out = tokenizer.apply_chat_template(probe, tokenize=False, **kwargs)
    except Exception:                                   # noqa: BLE001
        return None
    return out if isinstance(out, str) else None


def detect_thinking_format(tokenizer, name: str = "detected") -> "ThinkingFormat | None":
    """Work out the thinking delimiters by rendering the tokenizer's own template.

    The trick: rendering a generation prompt with `enable_thinking=False`
    typically inserts an EMPTY reasoning block, so that render is the
    `enable_thinking=True` render plus exactly the closing marker. Diffing the
    two isolates the close delimiter without guessing at its spelling, and
    tells us the template opens the block itself.

    Returns None if the tokenizer does not expose enough to be sure -- an
    honest None beats a confident wrong answer here.
    """
    on = _render(tokenizer, add_generation_prompt=True, enable_thinking=True)
    off = _render(tokenizer, add_generation_prompt=True, enable_thinking=False)

    close_token = None
    open_in_prompt = False

    if on and off and off.startswith(on) and len(off) > len(on):
        close_token = off[len(on):]
        open_in_prompt = True
    elif on and off and on.startswith(off) and len(on) > len(off):
        # Inverted convention: the *thinking* render carries the extra marker.
        open_in_prompt = True

    # Strongest evidence first: the template's own source. A template that
    # concatenates 'OPEN' + reasoning + 'CLOSE' has told us the answer outright,
    # and no amount of render-diffing beats reading it.
    pair = _pair_from_template(_chat_template_source(tokenizer))
    if pair:
        open_token, close_token = pair
        if not open_in_prompt:
            plain = _render(tokenizer, add_generation_prompt=True)
            if any(r and r.endswith(open_token) for r in (on, plain)):
                open_in_prompt = True
        return ThinkingFormat(open_token=open_token, close_token=close_token,
                              name=name, open_emitted_by_template=open_in_prompt)

    # Locate the opening marker as the tail of a generation prompt, starting at
    # the last special token, and only accept it if it names a reasoning
    # channel rather than being an ordinary turn header.
    plain = _render(tokenizer, add_generation_prompt=True)
    open_token = None
    for render in (on, plain):
        if not render:
            continue
        specials = [t for t in _special_tokens(tokenizer) if t]
        cut = max((render.rfind(t) for t in specials), default=-1)
        if cut != -1:
            candidate = render[cut:]
            if any(w in candidate.lower() for w in _THINK_WORDS):
                open_token = candidate
                break

    if close_token is None:
        # Fall back to a special token that names a reasoning channel and looks
        # like a closer.
        closers = [t for t in _special_tokens(tokenizer)
                   if any(w in t.lower() for w in _THINK_WORDS)
                   and ("/" in t or t.startswith("</") or "|>" in t)]
        if len(closers) == 1:
            close_token = closers[0]

    if open_token is None and close_token is not None:
        # Close found but no render revealed the opener: pair it with a
        # reasoning-named special token that is not itself a closer.
        openers = [t for t in _special_tokens(tokenizer)
                   if t != close_token
                   and any(w in t.lower() for w in _THINK_WORDS)
                   and not (t.startswith("</") or "/" in t)]
        if len(openers) == 1:
            open_token = openers[0]

    # When the template rejects or ignores `enable_thinking`, the diff above
    # settles nothing. But if a generation prompt ENDS with the opening marker,
    # the template is opening the block whatever the kwarg did.
    if open_token and not open_in_prompt:
        if any(r and r.endswith(open_token) for r in (on, plain)):
            open_in_prompt = True

    if close_token is None or open_token is None:
        return None

    return ThinkingFormat(
        open_token=open_token,
        close_token=close_token,
        name=name,
        open_emitted_by_template=open_in_prompt,
    )


def _special_tokens(tokenizer) -> list[str]:
    """Every special token this tokenizer knows, longest first."""
    tokens: set[str] = set()
    for attr in ("all_special_tokens", "additional_special_tokens"):
        tokens.update(t for t in (getattr(tokenizer, attr, None) or []) if isinstance(t, str))
    decoder = getattr(tokenizer, "added_tokens_decoder", None) or {}
    for value in decoder.values():
        content = getattr(value, "content", value)
        if isinstance(content, str):
            tokens.add(content)
    return sorted(tokens, key=len, reverse=True)


# CONFIRMED against google/gemma-4-E4B-it (transformers 5.0.0). Its chat
# template contains, literally:
#
#     {{- '<|channel>thought\n' + thinking_text + '\n<channel|>' -}}
#
# so the model emits BOTH markers itself and the generation prompt ends at
# '<|turn>model\n'. open_emitted_by_template is therefore False.
#
# Thinking is switched on by a separate control token, <|think|>, which the
# template injects into the first system turn when enable_thinking=True -- not
# by pre-opening a channel. See docs/GEMMA4_FORMAT.md.
#
# resolve_from_tokenizer still re-derives all of this at load time, so a
# different checkpoint or a template revision corrects these rather than
# silently disagreeing with them.
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

    # When the chat template opens the block, the model's own output starts
    # inside it and legitimately carries no opening delimiter. Demanding one
    # would score every correct generation as a format failure.
    open_optional = fmt.open_emitted_by_template

    if n_open == 0 and not open_optional:
        errors.append("missing opening delimiter")
    if n_close == 0:
        errors.append("missing closing delimiter")
    if n_open > 1:
        errors.append(f"{n_open} opening delimiters, expected exactly 1")
    if n_open == 1 and open_optional and not text.lstrip().startswith(fmt.open_token):
        errors.append("opening delimiter appears mid-text; the template already emitted one")
    if n_close > 1:
        errors.append(f"{n_close} closing delimiters, expected exactly 1")
    if errors:
        return Parsed(thinking="", answer="", ok=False, errors=errors)

    end = text.index(fmt.close_token)
    if n_open:
        start = text.index(fmt.open_token)
        if end < start:
            return Parsed("", "", False, ["closing delimiter precedes opening delimiter"])
        thinking_start = start + len(fmt.open_token)
    else:
        start = 0
        thinking_start = 0

    thinking = text[thinking_start:end]
    answer = text[end + len(fmt.close_token) :]

    if not thinking.strip():
        errors.append("empty reasoning block")
    if not answer.strip():
        errors.append("empty final answer")
    if n_open and text[:start].strip():
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
