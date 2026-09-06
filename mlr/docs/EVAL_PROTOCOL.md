# Evaluation protocol

Written before training, per protocol item 5. Committed ahead of any results
so the metrics cannot be chosen to flatter them afterwards.

## The held-out set

`data/eval/held_out_v1.jsonl` — 12 reasoning problems x 4 languages = **48
items**. Disjoint from the 20-example training sample; `scripts/build_sample.py`
fails the build if any question collides.

Domains: arithmetic, division, percentage, rate, time, calendar, algebra,
comparison, logic.

Two deliberate design choices:

- **Gold answers are numeric wherever possible** (11 of 12 problems). A numeric
  answer is identical in all four languages, so correctness measures reasoning
  and cannot be contaminated by the language measurement. The two questions —
  did it reason correctly, and did it answer in the right language — stay
  genuinely independent.
- **Clock times are 24-hour digits.** Traditional Swahili time runs six hours
  offset from the clock, so a word-form time question would test cultural
  convention rather than arithmetic and would score Swahili unfairly.

**Size caveat.** 12 items per language is enough to expose gross language
collapse, which is the primary risk, but not to resolve small accuracy
differences — at n=12 a single item moves the rate by 8 points. Grow to ~50
problems per language before treating any before/after accuracy gap as real.
Language-collapse rates are usable at this size because the effect is large.

## What is measured

Three separate channels, never collapsed into one number.

### 1. Reasoning correctness — `reasoning_correct`
Judged on the **final answer only**, after the think block. The reasoning text
is free-form and is never string-matched. Numeric answers compare the last
number stated, since models restate their working before committing.

### 2. Language fidelity — measured twice, separately
- `reasoning_lang_ok` — is the **think block** in the requested language?
- `answer_lang_ok` — is the **final answer** in the requested language?

Split because the failure has two shapes and one number hides both:

- reasons in English, answers in Wolof — looks fine to anyone reading only the
  answer, but the model is not reasoning in the target language at all;
- reasons in Wolof, answers in English — the classic low-resource collapse,
  losing the language exactly where it matters.

`collapse_to_english` reports the union: any non-English item where either
channel came back English. This is the headline low-resource failure and it
gets its own line in every report.

### 3. Format integrity — `format_ok`
Reported on its own and never folded into correctness. If a fine-tune breaks
the think-block format, correctness craters; without a separate format channel
that looks like a reasoning regression when it is really a formatting bug.

### Headline number — `correct_and_in_language`
Right answer **and** reasoning in-language **and** answer in-language **and**
format intact. This is the number the project is trying to move.

## The Wolof scoring question, unresolved

Wolof speakers ordinarily count and do arithmetic in French, so some French in
a Wolof trace is natural speech rather than collapse. `WOLOF_FRENCH_TOLERANCE`
in `src/mlr/evaluation.py` is the share of French above which a Wolof response
is called collapsed. It is currently **0.40, a placeholder with no evidence
behind it**, and it is the first question in
`docs/WOLOF_REVIEW_PACKET.md`.

Every reported Wolof figure must state the tolerance it was computed with;
`aggregate()` puts it in the report so this cannot be forgotten.

## Running it

```bash
# CPU, GGUF quant -- the realistic path without an accelerator
python -m mlr.baseline --backend llamacpp --gguf /path/to/gemma-4-E4B-Q4_K_M.gguf

# GPU
python -m mlr.baseline --backend transformers --model-id google/gemma-4-E4B-it
```

Greedy decoding (temperature 0) so the baseline is reproducible, and one
system prompt shared across all four languages so no language is given extra
help. Raw generations are always written next to the scores: when a number
looks surprising, the raw text is the only way to tell a model failure from a
harness bug.

## Order of operations

1. Baseline untouched Gemma 4 on all 48 items. **Not yet done — blocked.**
2. Native-validate the training data.
3. LoRA fine-tune.
4. Re-run this same set, unchanged, and compare.

Changing the eval set between steps 1 and 4 invalidates the comparison. If it
has to change, re-run the baseline too.
