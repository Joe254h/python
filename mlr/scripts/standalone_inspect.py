#!/usr/bin/env python3
"""Standalone copy of the chat-template diagnostic, for pasting into a cell.

Deliberately duplicates scripts/inspect_chat_template.py with zero imports
from mlr, because the situation it exists for is "the repo checkout is stale
or missing". Paste the whole file into one Kaggle or Colab cell and run it.

scripts/inspect_chat_template.py is the maintained version and shares the
library's detection logic; this one is kept in step by hand. Verified
against four tokenizer conventions: channel-style, <think> tags, templates
that reject enable_thinking, and templates where the model emits both markers.
"""
import os
import transformers
from transformers import AutoTokenizer

MODEL = os.environ.get("BASE_MODEL", "google/gemma-4-E4B-it")
TOKEN = os.environ.get("HF_TOKEN") or None
THINK_WORDS = ("thought", "think", "channel", "analysis", "reasoning")
RULE = "-" * 74

print(f"transformers {transformers.__version__}\nmodel        {MODEL}")
tok = AutoTokenizer.from_pretrained(MODEL, **({"token": TOKEN} if TOKEN else {}))


def special_tokens(t):
    out = set()
    for attr in ("all_special_tokens", "additional_special_tokens"):
        out.update(x for x in (getattr(t, attr, None) or []) if isinstance(x, str))
    for v in (getattr(t, "added_tokens_decoder", None) or {}).values():
        c = getattr(v, "content", v)
        if isinstance(c, str):
            out.add(c)
    return sorted(out, key=len, reverse=True)


def show(label, value):
    print(f"\n{label}\n{RULE}")
    print(value if value else "(nothing)")


specials = special_tokens(tok)
show("ALL SPECIAL TOKENS", "\n".join(f"  {s!r}" for s in specials))
show("TOKENS NAMING A REASONING CHANNEL",
     "\n".join(f"  {s!r}" for s in specials
               if any(w in s.lower() for w in THINK_WORDS)))

probe = [{"role": "user", "content": "__PROBE__"}]
renders = {}
for label, kw in (("enable_thinking=True", {"enable_thinking": True}),
                  ("enable_thinking=False", {"enable_thinking": False}),
                  ("no enable_thinking kwarg", {})):
    try:
        renders[label] = tok.apply_chat_template(
            probe, tokenize=False, add_generation_prompt=True, **kw)
    except Exception as exc:
        renders[label] = f"<raised {type(exc).__name__}: {exc}>"
    show(f"GENERATION PROMPT — {label}", f"  {renders[label]!r}")

on, off = renders["enable_thinking=True"], renders["enable_thinking=False"]
close_token = open_token = None
open_in_prompt = False

if isinstance(on, str) and isinstance(off, str):
    if off.startswith(on) and len(off) > len(on):
        close_token, open_in_prompt = off[len(on):], True
        show("DIFF", f"  enable_thinking=False adds: {close_token!r}\n"
                     "  => the template OPENS the reasoning block itself\n"
                     "  => generated text has NO opening marker\n"
                     "  => training targets must NOT include one")
    elif on == off:
        show("DIFF", "  identical — this template may ignore enable_thinking")
    else:
        show("DIFF", "  differ unexpectedly; compare the two renders above by eye")

plain = renders["no enable_thinking kwarg"]
for render in (on, plain):
    if not isinstance(render, str):
        continue
    cut = max((render.rfind(t) for t in specials if t), default=-1)
    if cut != -1 and any(w in render[cut:].lower() for w in THINK_WORDS):
        open_token = render[cut:]
        break

if close_token is None:
    closers = [t for t in specials if any(w in t.lower() for w in THINK_WORDS)
               and ("/" in t or t.startswith("</") or "|>" in t)]
    if len(closers) == 1:
        close_token = closers[0]

if open_token is None and close_token is not None:
    openers = [t for t in specials if t != close_token
               and any(w in t.lower() for w in THINK_WORDS)
               and not (t.startswith("</") or "/" in t)]
    if len(openers) == 1:
        open_token = openers[0]

# If a generation prompt ENDS with the opening marker, the template opens the
# block -- true even when enable_thinking was rejected and the diff told us
# nothing.
if open_token and not open_in_prompt:
    if any(isinstance(r, str) and r.endswith(open_token) for r in (on, plain)):
        open_in_prompt = True

template = getattr(tok, "chat_template", "") or ""
if isinstance(template, dict):
    template = template.get("default") or next(iter(template.values()), "")
hits = [ln.strip() for ln in str(template).splitlines()
        if any(w in ln.lower() for w in THINK_WORDS)]
show("CHAT TEMPLATE LINES MENTIONING A REASONING CHANNEL",
     "\n".join(f"  {h}" for h in hits[:25]))

if open_token and close_token:
    show("RESULT — paste into src/mlr/format_guard.py",
         f"""GEMMA4_THINKING = ThinkingFormat(
    open_token={open_token!r},
    close_token={close_token!r},
    name="gemma4",
    open_emitted_by_template={open_in_prompt!r},
)""")
else:
    show("RESULT", "  Detection incomplete — send me the renders above and I'll\n"
                   "  read the delimiters off them.")
