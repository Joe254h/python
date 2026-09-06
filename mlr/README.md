# Four-language reasoning on Gemma 4

On-device multilingual reasoning restricted to **Swahili, Wolof, English and
French**, keeping the model's thinking rather than only its answers.

Base model: **Gemma 4 E4B** (4.5B, on-device size, built-in thinking mode,
covers both Swahili and Wolof).

## Status

| protocol item | state |
|---|---|
| 1. Zero-shot baseline in 4 languages | **Blocked.** Harness written and tested; Gemma 4 unreachable |
| 2. Quality over quantity, provenance logged | 20 examples drafted; Swahili reviewed, Wolof pending native review |
| 3. Protect the think-block format | Done, enforced automatically |
| 4. LoRA / QLoRA fine-tune | Not started (correctly — core first) |
| 5. Evaluation defined before training | Done and committed ahead of any results |
| 6. Quantize and measure on device | Phase two, not started |

**There is no baseline number in this repository, and nothing here should be
presented as one.** `huggingface.co` and every other model host are blocked by
this environment's egress policy, so Gemma 4 has never been run here. See
[`docs/BLOCKERS.md`](docs/BLOCKERS.md).

## What is here

```
src/mlr/
  format_guard.py   think-block parsing and translation integrity  (item 3)
  langid.py         sw/wo/en/fr identification + code-switch measurement
  evaluation.py     the metrics, defined before training           (item 5)
  backends.py       transformers / llama.cpp / scripted mock
  baseline.py       the zero-shot runner                           (item 1)
data/
  eval/held_out_v1.jsonl    48 held-out items (12 problems x 4 languages)
  sample20/                 the 20-example sample + per-example provenance
docs/
  BLOCKERS.md               what is blocked and how to unblock it
  DATA_PLAN.md              what the upstream dataset actually contains
  EVAL_PROTOCOL.md          the metrics, committed before results
  SWAHILI_REVIEW.md         Swahili review record and corrections found
  WOLOF_REVIEW_PACKET.md    the packet for the native Wolof reviewer
```

## Reproduce

```bash
python3 -m unittest discover -s tests            # 17 tests, no dependencies
python3 scripts/build_eval_set.py                # held-out set
python3 scripts/build_sample.py                  # validate + emit the 20 samples
python3 scripts/make_wolof_packet.py             # native-review packet
python3 scripts/selftest_harness.py              # pipeline check (NOT a baseline)
```

Once weights are reachable:

```bash
python3 -m mlr.baseline --backend llamacpp --gguf gemma-4-E4B-Q4_K_M.gguf
```

## How the evaluation works

Three things are measured separately and never collapsed into one number:
whether the reasoning is **correct**, whether the **think block** is in the
requested language, and whether the **final answer** is in the requested
language. The low-resource failure this project exists to catch — a model that
reasons in English and collapses back to English for a Wolof question — is
only visible when the last two are kept apart. Format integrity is a fourth,
separate channel so a formatting bug cannot masquerade as a reasoning
regression.

Full rationale in [`docs/EVAL_PROTOCOL.md`](docs/EVAL_PROTOCOL.md).

## Verification status of the data

Nothing carries `human_verified: true`. Swahili is `model_checked` — read
against a grammatical checklist by a model, which is not native validation.
Wolof is `model_translated` and must not be trained on or evaluated against
until a native speaker has been through
[`docs/WOLOF_REVIEW_PACKET.md`](docs/WOLOF_REVIEW_PACKET.md).
