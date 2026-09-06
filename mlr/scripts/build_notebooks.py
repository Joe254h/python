#!/usr/bin/env python3
"""Generate the Colab and Kaggle notebooks.

Generated rather than hand-written so the two stay in sync: they differ only
in platform setup (secrets, paths, GPU capability) and run the identical
training and evaluation code from src/mlr. Hand-maintained notebooks drift,
and a notebook that has drifted from the library is worse than no notebook.

    python scripts/build_notebooks.py
"""

import sys
from pathlib import Path

import nbformat as nbf

REPO = "https://github.com/Joe254h/python.git"
BRANCH = "claude/gemma-4-multilingual-reasoning-xqse1j"
OUT = Path("notebooks")

# --------------------------------------------------------------------------
# Cells shared by both platforms. Only setup and persistence differ.
# --------------------------------------------------------------------------

def intro(platform: str, gpu_note: str) -> str:
    return f"""# Four-language reasoning on Gemma 4 — {platform}

Swahili · Wolof · English · French, keeping the model's **thinking**, not just
its answers.

This notebook runs the whole loop in the order the protocol requires:

1. **Baseline first.** Zero-shot Gemma 4 on the held-out set, *before* any
   training. Without a "before" there is nothing to prove an improvement against.
2. Fine-tune with QLoRA (frozen base, adapters only).
3. Re-run the *same* held-out set and compare.
4. Save the adapter so the web application can serve it.

**Two things are measured separately and never merged:** whether the reasoning
is correct, and whether the model answered in the language it was asked in. The
classic low-resource failure is a model that reasons in English and collapses
back to English for a Wolof question — that only shows up when you keep the two
apart.

{gpu_note}

> **Data status.** Nothing in the sample is natively verified yet. Wolof in
> particular is unverified machine translation. The training script *refuses*
> to run on unverified rows unless you pass `--allow-unverified`, which marks
> the resulting model card as a pipeline test. Do not report numbers from such
> a run — get the Wolof native review done first (`docs/WOLOF_REVIEW_PACKET.md`).
"""


CELLS_COMMON_A = [
    ("md", """## 1. Get the code

Everything below calls the shared library in `src/mlr/`, the same code the HPC
job runs. No logic is duplicated in this notebook.

This cell works two ways: it uses the project if you already uploaded and
unzipped it, and otherwise clones it from GitHub. Either route leaves you in
the project root."""),
    ("code", f"""import os, pathlib, subprocess

def _find_project(start="."):
    # Look for a directory containing src/mlr: here first, then one level down.
    root = pathlib.Path(start).resolve()
    if (root / "src" / "mlr").is_dir():
        return root
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if (child / "src" / "mlr").is_dir():
            return child
    return None

project = _find_project()
if project is None:
    subprocess.run(["git", "clone", "--branch", "{BRANCH}",
                    "--single-branch", "{REPO}", "repo"], check=True)
    project = _find_project("repo")

os.chdir(project)
print("project root:", os.getcwd())
assert pathlib.Path("src/mlr/evaluation.py").exists(), "project files not found"
print("contents:", sorted(p.name for p in pathlib.Path(".").iterdir())[:12])"""),
    ("md", """## 2. Install

`transformers`, `peft`, `bitsandbytes` for QLoRA. The project's own code —
format guard, language ID, evaluation — needs nothing beyond the standard
library, which is why the test suite below runs instantly."""),
    ("code", """%pip install -q "transformers>=4.57" "peft>=0.14" "accelerate>=1.0" "bitsandbytes>=0.44" "datasets>=3.0"
print("installed")"""),
    ("md", """## 3. Check the harness before trusting any number it produces

17 tests covering the think-block format guard, four-language identification,
and — most importantly — that the evaluation actually detects both directions
of language collapse. If these fail, stop: every later number is meaningless."""),
    ("code", """!python -m unittest discover -s tests 2>&1 | tail -5"""),
]

CELLS_COMMON_B = [
    ("md", """## 5. Confirm how this model marks its reasoning block

Tokenizer only, no weights, a few seconds. Every model family spells its
thinking delimiters differently, and the one detail that matters most is
whether the chat template *opens* the reasoning block itself: if it does, the
model's output carries no opening marker, and a training target that includes
one teaches a duplicate.

The pipeline resolves this automatically at load time. This cell just shows
you what it resolved, so a surprise here is visible in seconds rather than
after an hour of training."""),
    ("code", """import os
BASE_MODEL = os.environ.get("BASE_MODEL", "google/gemma-4-E4B-it")
!python scripts/inspect_chat_template.py --model $BASE_MODEL"""),
    ("md", """## 6. Build the data

The held-out evaluation set (48 items) and the 20-example training sample.
`build_sample.py` is adversarial towards its own input: it fails the build if
a think block is broken, if the numbers drift between languages, or if a
training question collides with a held-out one."""),
    ("code", """!python scripts/build_eval_set.py
!python scripts/build_sample.py"""),
    ("md", """## 7. BASELINE — run this before training

Protocol item 1. Zero-shot, greedy decoding, one shared system prompt across
all four languages so no language gets extra help.

This takes a while: a thinking model generates a few hundred tokens per item,
48 items. Raw generations are saved next to the scores — when a number looks
surprising, the raw text is the only way to tell a model failure from a
harness bug."""),
    ("code", """!python scripts/run_eval.py --mode baseline --base $BASE_MODEL --out results {FP16_FLAG}"""),
    ("code", """# The "before" table. Keep it — this is what the fine-tune has to beat.
print(open("results/baseline/baseline_table.txt").read())"""),
    ("md", """## 8. Fine-tune with QLoRA

Base frozen in 4-bit, LoRA adapters trained on top. Rank 16 is deliberate for a
few-hundred-example corpus — a larger adapter mostly memorises.

LoRA target modules are **discovered from the loaded model**, not hardcoded, so
this still targets the right projections if Gemma 4 names them differently from
earlier releases.

`--allow-unverified` is present because the Wolof review has not happened yet.
Remove it once it has."""),
    ("code", """!python scripts/train_lora.py \\
    --data data/sample20/sample20.jsonl \\
    --base $BASE_MODEL \\
    --out artifacts/adapter \\
    --epochs 3 --lora-r 16 \\
    --allow-unverified {FP16_FLAG}"""),
    ("md", """## 9. Evaluate the fine-tune and compare

Same held-out set, unchanged. Changing the eval between the before and after
would invalidate the comparison."""),
    ("code", """!python scripts/run_eval.py --mode adapter --base $BASE_MODEL --adapter artifacts/adapter --out results {FP16_FLAG}
print(open("results/finetuned/baseline_table.txt").read())"""),
    ("code", """import json
# Merge the two runs into the comparison the web application reads.
base = json.load(open("results/baseline/baseline_report.json"))["summary"]
tuned = json.load(open("results/finetuned/baseline_report.json"))["summary"]
card = json.load(open("artifacts/adapter/model_card.json"))

metrics = ("reasoning_correct", "reasoning_lang_ok", "answer_lang_ok",
           "collapse_to_english", "correct_and_in_language")
deltas = {lang: {m: round(tuned["by_language"][lang][m] - base["by_language"][lang][m], 4)
                 for m in metrics}
          for lang in base["by_language"]}

json.dump({"base_model": BASE_MODEL, "adapter": "artifacts/adapter",
           "model_card": card, "baseline": base, "finetuned": tuned,
           "deltas": deltas},
          open("results/comparison.json", "w"), indent=2, ensure_ascii=False)

print(f"{'lang':>5}  {'correct':>9} {'in-language':>12} {'collapse-EN':>12}")
for lang, d in deltas.items():
    print(f"{lang:>5}  {d['reasoning_correct']:>+9.0%} "
          f"{d['correct_and_in_language']:>+12.0%} {d['collapse_to_english']:>+12.0%}")"""),
    ("md", """## 10. Export for the web application

Writes `serve_manifest.json` — the contract the web app reads. It names the
artifact kind, the thinking delimiters, the data fingerprint, and whether the
model was trained on unverified data (the app displays that prominently)."""),
    ("code", """!python scripts/export_model.py --adapter artifacts/adapter --base $BASE_MODEL --out artifacts/serve --kind adapter
!cat artifacts/serve/serve_manifest.json"""),
]

CELLS_WEBAPP = [
    ("md", """## 12. Try the web application

Serves live four-language inference — showing the think block and the final
answer separately, with language detection on each — plus the before/after
comparison and the data verification status.

Loading the model into the app takes a few minutes. Interrupt the cell to stop."""),
    ("code", """%pip install -q fastapi uvicorn
# --stub runs the UI with no model, useful for checking the interface first.
!python webapp/server.py --manifest artifacts/serve/serve_manifest.json --port 8000 &"""),
]


def colab_cells():
    fp16 = ""
    cells = [("md", intro("Google Colab",
        "**Runtime → Change runtime type → T4 GPU** (or better) before running. "
        "A T4's 16 GB is enough for E4B with a 4-bit base."))]
    cells += CELLS_COMMON_A[:1]
    cells += [
        ("md", "## 0. Confirm the GPU"),
        ("code", """import subprocess
print(subprocess.run(["nvidia-smi","--query-gpu=name,memory.total","--format=csv"],
                     capture_output=True, text=True).stdout or
      "NO GPU -- set Runtime > Change runtime type > T4 GPU")"""),
    ]
    cells += CELLS_COMMON_A[1:]
    cells += [
        ("md", """## 4. Authenticate with Hugging Face

Gemma 4 is a **gated** model: accept the licence on its model page first, then
add your token to Colab secrets (the key icon in the left sidebar) as
`HF_TOKEN` and enable notebook access."""),
        ("code", """from google.colab import userdata
import os
try:
    os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
    print("HF token loaded from Colab secrets")
except Exception as e:
    print(f"No HF_TOKEN secret found ({e}).")
    print("Add it via the key icon in the sidebar, or run: "
          "from huggingface_hub import login; login()")"""),
    ]
    cells += CELLS_COMMON_B
    cells += [
        ("md", """## 11. Save to Google Drive

Colab runtimes are wiped when they disconnect. The adapter is small (tens of
MB), so copying it to Drive costs little and keeps the run reproducible."""),
        ("code", """from google.colab import drive
drive.mount("/content/drive")

import shutil, pathlib
dest = pathlib.Path("/content/drive/MyDrive/gemma4-mlr")
dest.mkdir(parents=True, exist_ok=True)
shutil.copytree("artifacts/serve", dest / "serve", dirs_exist_ok=True)
shutil.copytree("results", dest / "results", dirs_exist_ok=True)
print(f"saved to {dest}")
print(sorted(p.name for p in dest.rglob("*") if p.is_file())[:20])"""),
    ]
    cells += CELLS_WEBAPP
    cells += [("code", """# Colab cannot open a port directly -- tunnel it.
from google.colab import output
output.serve_kernel_port_as_window(8000)""")]
    return [(t, s.replace("{FP16_FLAG}", fp16)) for t, s in cells]


def kaggle_cells():
    fp16 = "--fp16"
    cells = [("md", intro("Kaggle",
        "**Settings → Accelerator → GPU T4 x2** (or P100), and **Internet: On** "
        "— the model download needs it.\n\n"
        "> Kaggle's P100 does not support bfloat16, so the training and "
        "evaluation cells below pass `--fp16`. On T4 either works."))]
    cells += [
        ("md", "## 0. Confirm the GPU and internet access"),
        ("code", """import subprocess, socket
print(subprocess.run(["nvidia-smi","--query-gpu=name,memory.total","--format=csv"],
                     capture_output=True, text=True).stdout or "NO GPU -- enable it in Settings")
try:
    socket.create_connection(("huggingface.co", 443), timeout=5)
    print("internet: ON")
except OSError:
    print("internet: OFF -- enable it in Settings, the model cannot download otherwise")"""),
    ]
    cells += CELLS_COMMON_A
    cells += [
        ("md", """## 4. Authenticate with Hugging Face

Gemma 4 is **gated**: accept the licence on its model page, then add your token
under **Add-ons → Secrets** as `HF_TOKEN`."""),
        ("code", """import os
from kaggle_secrets import UserSecretsClient
try:
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
    print("HF token loaded from Kaggle secrets")
except Exception as e:
    print(f"No HF_TOKEN secret found ({e}). Add it under Add-ons > Secrets.")"""),
    ]
    cells += CELLS_COMMON_B
    cells += [
        ("md", """## 11. Persist the outputs

Everything under `/kaggle/working` is saved when the notebook commits, and can
be attached to other notebooks — or downloaded — as a dataset. The adapter is
small enough that this is cheap."""),
        ("code", """import shutil, pathlib
dest = pathlib.Path("/kaggle/working/gemma4-mlr")
dest.mkdir(parents=True, exist_ok=True)
shutil.copytree("artifacts/serve", dest / "serve", dirs_exist_ok=True)
shutil.copytree("results", dest / "results", dirs_exist_ok=True)
print(f"saved to {dest}")
for p in sorted(dest.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(dest)}  ({p.stat().st_size/1e6:.1f} MB)")"""),
        ("md", """## 12. Web application

Kaggle does not expose arbitrary ports, so run the app locally instead: commit
this notebook, download `gemma4-mlr/serve` from the output, and serve it with

```bash
python webapp/server.py --manifest serve/serve_manifest.json
```"""),
    ]
    return [(t, s.replace("{FP16_FLAG}", fp16)) for t, s in cells]


def build(cells, path: Path, display_name: str) -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(s) if t == "md" else nbf.v4.new_code_cell(s)
                for t, s in cells]
    nb.metadata = {
        "kernelspec": {"display_name": display_name, "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "accelerator": "GPU",
    }
    nbf.validate(nb)
    path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, str(path))
    print(f"wrote {path}  ({len(nb.cells)} cells)")


def main() -> int:
    build(colab_cells(), OUT / "colab_gemma4_multilingual_reasoning.ipynb", "Python 3")
    build(kaggle_cells(), OUT / "kaggle_gemma4_multilingual_reasoning.ipynb", "Python 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
