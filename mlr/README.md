# Four-language reasoning on Gemma 4

On-device multilingual reasoning restricted to **Swahili, Wolof, English and
French**, keeping the model's thinking rather than only its answers.

Base model: **Gemma 4 E4B** (4.5B, on-device size, built-in thinking mode,
covers both Swahili and Wolof).

## Status

| protocol item | state |
|---|---|
| 1. Zero-shot baseline in 4 languages | **Blocked here.** Harness written and tested; no model host reachable from this environment |
| 2. Quality over quantity, provenance logged | 20 examples; Swahili reviewed, Wolof pending native review |
| 3. Protect the think-block format | Done, enforced automatically |
| 4. LoRA / QLoRA fine-tune | Code written and testable; never executed (no GPU here) |
| 5. Evaluation defined before training | Done and committed ahead of any results |
| 6. Quantize and measure on device | Export path written; not run |

**No number in this repository came from Gemma 4.** `huggingface.co` and every
other model host are blocked by this environment's egress policy, and there is
no GPU. Everything that does not need weights has been run and is green: 17
tests, the data build, the format guard, and the web application. See
[`docs/BLOCKERS.md`](docs/BLOCKERS.md).

## Run it

Three surfaces, **one implementation** — the notebooks and the HPC job both
call `scripts/train_lora.py`, which calls `src/mlr/training.py`. Nothing is
duplicated per platform, so nothing drifts.

| where | how |
|---|---|
| **Colab** | open `notebooks/colab_gemma4_multilingual_reasoning.ipynb`, set Runtime → T4 GPU |
| **Kaggle** | open `notebooks/kaggle_gemma4_multilingual_reasoning.ipynb`, GPU + Internet on |
| **HPC** | `bash scripts/hpc/setup_env.sh` on a login node, then `sbatch scripts/hpc/train.slurm` |
| **Web app** | `python webapp/server.py --stub` (no model needed to see the interface) |

The order matters and the notebooks enforce it: **baseline before training.**
Without a "before" there is nothing to prove an improvement against.

```bash
python3 -m unittest discover -s tests     # 17 tests, standard library only
python3 scripts/build_eval_set.py         # 48 held-out items
python3 scripts/build_sample.py           # validate + emit the 20 samples
python3 scripts/run_eval.py --mode baseline   # the "before"     (needs weights)
python3 scripts/train_lora.py                 # QLoRA fine-tune  (needs a GPU)
python3 scripts/run_eval.py --mode compare    # before vs after
python3 scripts/export_model.py               # artifact for the web app
python3 webapp/server.py --manifest artifacts/serve/serve_manifest.json
```

## Layout

```
src/mlr/
  format_guard.py   think-block parsing and translation integrity  (item 3)
  langid.py         sw/wo/en/fr identification + code-switch measurement
  evaluation.py     the metrics, defined before training           (item 5)
  data.py           corpus assembly; refuses unverified rows       (item 2)
  training.py       QLoRA config and trainer                       (item 4)
  backends.py       transformers / llama.cpp / scripted mock
  baseline.py       the zero-shot runner                           (item 1)
scripts/
  build_eval_set.py build_sample.py make_wolof_packet.py
  train_lora.py     run_eval.py     export_model.py
  build_notebooks.py                hpc/{setup_env.sh,train.slurm}
notebooks/          Colab and Kaggle, generated from build_notebooks.py
webapp/             FastAPI server + single-page UI
data/               held-out eval set, 20-example sample, provenance log
docs/               blockers, data plan, eval protocol, language reviews
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

The web app renders the same three facts per response, using the same code, so
the demo and the metrics cannot disagree.

Full rationale in [`docs/EVAL_PROTOCOL.md`](docs/EVAL_PROTOCOL.md).

## Verification status of the data

Nothing carries `human_verified: true`. Swahili is `model_checked` — read
against a grammatical checklist by a model, which is not native validation.
Wolof is `model_translated` and unreviewed.

`load_training_rows()` **refuses** to return unverified rows unless the caller
passes `allow_unverified=True`, and that choice is written into the model card
and displayed by the web app. The protocol is enforced in code, not just
documented, because a rule that lives only in a document gets forgotten at 2am
before a deadline.

Native Wolof review: [`docs/WOLOF_REVIEW_PACKET.md`](docs/WOLOF_REVIEW_PACKET.md).
