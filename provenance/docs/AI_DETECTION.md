# AI-writing detection

This document exists because the feature is dangerous when done carelessly, and
the careless version is the easy one to build.

## Why it is off by default

A Stanford-affiliated study found that seven publicly available detectors, GPTZero
and ZeroGPT among them, flagged **61.3% of TOEFL essays written by non-native
English speakers** as machine-generated, while performing almost perfectly on
essays by US eighth-graders. ([Liang et al., 2023](https://arxiv.org/pdf/2304.02819))

The mechanism is not mysterious. Second-language writers use common vocabulary
and regular syntax, and produce text with low perplexity under a language model.
That is the same signal every statistical detector keys on. A detector is
therefore not measuring "did a machine write this" so much as "is this text
unsurprising", and those two questions have very different answers depending on
who wrote it.

For a service used by students at an institution like AIMS — where most users
write academic English as a second or third language — this is not an edge case.
It is the defining failure mode of the feature.

So the code enforces a rule that a README cannot:

- `BinocularsDetector.score()` raises `UncalibratedError` if `calibration` is
  `None`. It cannot be persuaded to emit a probability without one.
- `load_detector()` returns `NullAiDetector` when no calibration file exists,
  and `NullAiDetector` returns an empty list.
- An empty list makes `Report.ai_probability` **`None`**, not `0.0`, and the UI
  renders *AI-writing detection did not run*. Absence is not innocence.
- Every `AiSignal` carries `fpr_at_threshold`, measured on the second-language
  control set. The number is in the payload because it belongs on the screen.

## The detector

[Binoculars](https://arxiv.org/abs/2401.12070) (Hans et al., ICML 2024). Score a
passage with two closely related models — an observer and a performer — and take
the ratio of the performer's perplexity to the cross-perplexity between the pair:

```
                perplexity(text under performer)
    B(text)  =  ─────────────────────────────────
                cross-perplexity(observer, performer)
```

Lower means more machine-like. The denominator is the important half: it
normalises away "this text is simply predictable", which is precisely the term
whose absence makes naive perplexity detectors punish second-language writing.
Reference implementation: [ahans30/Binoculars](https://github.com/ahans30/Binoculars).

Reported performance: over 90% of ChatGPT-generated samples detected at a 0.01%
false positive rate, zero-shot, beating commercial detectors including GPTZero.
Those numbers are from the paper's evaluation sets, not from yours — which is
the entire reason the calibration step exists.

### Model pair

| Pair | Runs on | Use |
|---|---|---|
| `Qwen/Qwen2.5-0.5B` + `-Instruct` | CPU | Default. Viable on a free web tier. |
| `tiiuae/falcon-7b` + `-instruct` | GPU | The paper's pair. Stronger; needs a Space or Kaggle. |

The pair is a constructor argument and **the calibration is fitted per pair** —
`Calibration.detector` records which one produced it. A calibration fitted for
Qwen is meaningless applied to Falcon.

## Fitting a calibration

You need four held-out sets. Build them before you look at any results, so the
threshold is not chosen to flatter the numbers.

| Set | Source | Purpose |
|---|---|---|
| Human, first-language | Pre-2020 student writing or corpora | Clean negative — cannot be contaminated by instruction-tuned models |
| **Human, second-language** | TOEFL-style essays, your own cohort with consent | **The control. This is the number you publish.** |
| Machine, in-distribution | Generated with the free LLM tiers | Positive |
| Machine, adversarial | Paraphrased, "humanised", edited machine text | The realistic positive |

Generate the machine sets with `detector.providers.Router` — Cerebras's 1M
tokens/day is exactly the budget for this, and it is the single best use of the
free tiers in this project.

Then:

1. Score every passage in every set with `BinocularsDetector.raw_score()`.
2. Fit a two-parameter logistic (Platt scaling) from raw score to probability.
3. Choose the threshold that yields **1% FPR on the second-language control
   set** — not on the combined negative set, which is a kinder and much less
   useful number. 1% is the bar because it matches the best false-positive
   result on the [RAID benchmark](https://gradpilot.com/news/ai-detector-false-positive-rates-compared).
4. Bootstrap the interval half-width.
5. Write `data/calibration.json` and point `PROVENANCE_CALIBRATION` at it.

```json
{
  "detector": "binoculars/Qwen2.5-0.5B",
  "slope": -4.0,
  "intercept": 3.6,
  "threshold": 0.9,
  "fpr_at_threshold": 0.01,
  "control_set": "aims-l2-control-v1",
  "n_control": 500,
  "interval_halfwidth": 0.12
}
```

Report **precision at fixed 1% FPR**, never accuracy. Accuracy on an imbalanced
set is a number that means nothing and flatters everything.

## Phase 5: when to fine-tune

Only if Phase 4's gate fails — recall at 1% FPR on *your* control set is
unacceptable. Fine-tuning is not free maintenance, and a model that loses to
Binoculars is a liability rather than an asset.

If it does fail: DeBERTa-v3-base or ModernBERT-base on Kaggle's T4 ×2, 30 GPU-hours
per week, 12-hour session cap. Training data from DAIGT-V2, HC3 and RAID, plus
your own generated pairs. Generate the notebook from a script the way
`mlr/scripts/build_notebooks.py` already does, rather than hand-editing JSON.

**Gate:** beats Binoculars on the same held-out sets at the same FPR. If it does
not, keep Binoculars and delete the model.

## What the report must never say

- A verdict. No "AI-generated: yes".
- A bare percentage with no interval and no stated FPR.
- A number merged with the similarity score. They measure different things and
  combining them is how these tools mislead.

What it should say is a probability, an interval, the false positive rate of the
threshold that produced it, and a sentence making clear this is evidence to
investigate with rather than grounds for an accusation.
