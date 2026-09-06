#!/usr/bin/env python3
"""Print exactly how a model marks its reasoning block. Tokenizer only, no weights.

Run this whenever a new base model is introduced, or when the format guard
says it cannot determine the format:

    python scripts/inspect_chat_template.py --model google/gemma-4-E4B-it

It downloads only the tokenizer and chat template (a few tens of MB, seconds),
prints the special tokens and both renders of the generation prompt with
`repr` so whitespace is visible, and ends with a line you can paste straight
into src/mlr/format_guard.py.

The renders are the important part. If the `enable_thinking=False` render is
the `True` render plus a trailing marker, the template opens the reasoning
block itself -- which means the model's output carries no opening marker, and
training targets must not include one either.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mlr.format_guard import (detect_thinking_format, _special_tokens,   # noqa: E402
                              _chat_template_source, _THINK_WORDS)

RULE = "-" * 74


def show(label: str, value) -> None:
    print(f"\n{label}\n{RULE}")
    print(value if value else "(nothing)")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--model", default="google/gemma-4-E4B-it")
    p.add_argument("--token", default="", help="HF token, if the model is gated")
    p.add_argument("--full-template", action="store_true",
                   help="dump the entire chat template source")
    args = p.parse_args(argv)

    import transformers
    from transformers import AutoTokenizer

    print(f"transformers {transformers.__version__}")
    print(f"model        {args.model}")

    kwargs = {"token": args.token} if args.token else {}
    tok = AutoTokenizer.from_pretrained(args.model, **kwargs)

    specials = _special_tokens(tok)
    show("ALL SPECIAL TOKENS", "\n".join(f"  {s!r}" for s in specials))

    reasoning = [s for s in specials if any(w in s.lower() for w in _THINK_WORDS)]
    show("SPECIAL TOKENS THAT NAME A REASONING CHANNEL",
         "\n".join(f"  {s!r}" for s in reasoning))

    probe = [{"role": "user", "content": "__PROBE__"}]
    renders = {}
    for label, kw in (("enable_thinking=True", {"enable_thinking": True}),
                      ("enable_thinking=False", {"enable_thinking": False}),
                      ("no enable_thinking kwarg", {})):
        try:
            renders[label] = tok.apply_chat_template(
                probe, tokenize=False, add_generation_prompt=True, **kw)
        except Exception as exc:                                # noqa: BLE001
            renders[label] = f"<raised {type(exc).__name__}: {exc}>"
        show(f"GENERATION PROMPT — {label}", f"  {renders[label]!r}")

    on, off = renders.get("enable_thinking=True"), renders.get("enable_thinking=False")
    if isinstance(on, str) and isinstance(off, str):
        if off.startswith(on) and len(off) > len(on):
            show("DIFF", f"  enable_thinking=False adds: {off[len(on):]!r}\n"
                         f"  => the template OPENS the reasoning block itself.\n"
                         f"  => generated text will NOT contain an opening marker.\n"
                         f"  => training targets must NOT include one either.")
        elif on == off:
            show("DIFF", "  identical — this template may ignore enable_thinking.")
        else:
            show("DIFF", f"  the two renders differ in a way this script did not\n"
                         f"  anticipate. Compare them by eye above.")

    template = _chat_template_source(tok)
    if args.full_template:
        show("CHAT TEMPLATE SOURCE", template)
    else:
        hits = [ln.strip() for ln in template.splitlines()
                if any(w in ln.lower() for w in _THINK_WORDS)]
        show("CHAT TEMPLATE LINES MENTIONING A REASONING CHANNEL",
             "\n".join(f"  {h}" for h in hits[:25]) +
             ("\n  (--full-template for all of it)" if hits else ""))

    fmt = detect_thinking_format(tok, name="gemma4")
    if fmt is None:
        show("RESULT", "  Detection FAILED. Read the renders above and set\n"
                       "  GEMMA4_THINKING in src/mlr/format_guard.py by hand.")
        return 1

    show("RESULT — paste this into src/mlr/format_guard.py",
         f"""GEMMA4_THINKING = ThinkingFormat(
    open_token={fmt.open_token!r},
    close_token={fmt.close_token!r},
    name="gemma4",
    open_emitted_by_template={fmt.open_emitted_by_template!r},
)""")
    print("\nDetection succeeded, so the pipeline resolves this automatically at\n"
          "load time. Pasting it in only removes the runtime lookup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
