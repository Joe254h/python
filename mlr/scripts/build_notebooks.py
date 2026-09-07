#!/usr/bin/env python3
"""Generate the Kaggle and Colab notebooks.

Generated, not hand-written, so the two cannot drift apart or away from the
library in src/mlr. They differ only in paths and secrets handling.

Design rules, each one earned from a real run that broke:

  * Every cell is self-sufficient. PROJECT is a literal constant re-stated in
    each cell rather than inherited from a previous cell's os.chdir, because a
    kernel restart or an out-of-order run silently resets the working directory
    and sends later cells looking in the wrong place.
  * The clone is deleted and re-made every run. A stale checkout that skips
    re-cloning is invisible and produces "file not found" for files that plainly
    exist on the branch.
  * The environment cell restarts the session itself when needed. An in-process
    pip upgrade does not affect an already-imported module, and a version floor
    that a preinstalled release already satisfies upgrades nothing at all.
  * Precision is detected, not chosen. T4 and P100 have no bfloat16; asking the
    user to pick a flag is asking them to get it wrong.
"""

import nbformat as nbf
from pathlib import Path

REPO = "https://github.com/Joe254h/python.git"
BRANCH = "claude/gemma-4-multilingual-reasoning-xqse1j"
OUT = Path("notebooks")


# --------------------------------------------------------------------------- 1
INTRO = """# Four-language reasoning on Gemma 4 — {platform}

Swahili · Wolof · English · French, keeping the model's **thinking**, not just
its answers.

Run the cells top to bottom. **Cell 2 may restart the session once** — that is
expected; when it does, just run it again and carry on.

## Before you start

1. **{accel}**
2. **{net}**
3. Accept the Gemma 4 licence on its Hugging Face model page.
4. Put your Hugging Face token in **{secrets}** as `HF_TOKEN`.

## What this does, in order

| cell | step |
|---|---|
| 2 | environment: GPU, dependencies, restart if needed |
| 3 | fresh clone, authenticate, run the test suite |
| 4 | confirm the thinking format, build the data |
| 5 | smoke test — 4 items, ~2 minutes |
| 6 | **baseline** — 48 items, the "before" measurement |
| 8 | QLoRA fine-tune |
| 9 | evaluate and compare against the baseline |
| 10 | export and save |

The baseline comes before the fine-tune on purpose. Without a "before" there is
nothing to prove an improvement against, and a good-looking number after
training proves nothing on its own.

> **Data status.** Nothing in the training sample has been verified by a native
> speaker; Wolof is unreviewed machine translation. Cell 8 passes
> `--allow-unverified`, which stamps the model card as a pipeline test. Numbers
> from such a run must not be reported. The baseline in cell 6 is unaffected —
> it uses the untouched base model and is a real measurement.
"""

# --------------------------------------------------------------------------- 2
ENV = '''# CELL 2 — environment. May restart the session once; that is expected.
import subprocess, sys, os

PACKAGES = ["transformers>=5.16", "peft>=0.14", "accelerate>=1.0",
            "bitsandbytes>=0.44", "datasets>=3.0"]

print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total",
                      "--format=csv,noheader"],
                     capture_output=True, text=True).stdout.strip()
      or "NO GPU — enable it in {accel_hint}")

print("\\ninstalling (quiet, ~1 min) ...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", *PACKAGES],
               check=True)

def _version(text):
    out = []
    for part in text.split(".")[:3]:
        digits = "".join(c for c in part if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)

import transformers
print("transformers", transformers.__version__)

# transformers below 5.16 cannot build a gemma4 config, and this process is
# still running whatever was imported before the upgrade -- so restart.
if _version(transformers.__version__) < (5, 16):
    print("\\n" + "=" * 70)
    print("RESTARTING THE SESSION to pick up the upgrade.")
    print("This is normal. When it finishes, RUN THIS CELL AGAIN and continue.")
    print("=" * 70)
    import IPython
    IPython.Application.instance().kernel.do_shutdown(True)
else:
    import torch
    BF16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    print(f"bfloat16 supported: {{BF16}}  ->  precision flag "
          f"{{'(bf16, default)' if BF16 else '--fp16'}}")
    print("\\nenvironment ready — continue to cell 3")
'''

# --------------------------------------------------------------------------- 3
SETUP = '''# CELL 3 — fresh clone, authentication, self-test.
import os, shutil, subprocess, sys

ROOT    = "{root}"
PROJECT = "{project}"
BRANCH  = "{branch}"
REPO    = "{repo}"

# Step OUT of the tree before deleting it. A previous run leaves this process
# standing inside repo/mlr; removing that directory leaves the process with a
# working directory that no longer exists, and every later subprocess fails
# with "Unable to read current working directory" -- including git clone, which
# needs a valid cwd even though it is creating a new directory elsewhere.
os.chdir(ROOT)

# Deleted and re-cloned every run. A stale checkout is invisible and produces
# "no such file" errors for files that plainly exist on the branch.
shutil.rmtree(f"{{ROOT}}/repo", ignore_errors=True)
subprocess.run(["git", "clone", "--depth", "1", "--branch", BRANCH,
                "--single-branch", REPO, f"{{ROOT}}/repo"], cwd=ROOT, check=True)
os.chdir(PROJECT)
print("project:", PROJECT)
print("commit :", subprocess.run(["git", "log", "--oneline", "-1"], cwd=PROJECT,
                                 capture_output=True, text=True).stdout.strip())

# Hugging Face token. Gemma 4 is gated.
{auth}

# The harness must be trustworthy before any number it produces means anything.
print("\\nrunning the test suite ...")
result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                        cwd=PROJECT, capture_output=True, text=True)
print(result.stderr.strip().splitlines()[-1])
assert result.returncode == 0, "tests failed — stop here, later numbers are meaningless"
'''

# --------------------------------------------------------------------------- 4
FORMAT_AND_DATA = '''# CELL 4 — confirm the thinking format, then build the data.
import os, subprocess, sys, torch

PROJECT = "{project}"
os.chdir(PROJECT)

BASE_MODEL = os.environ.get("BASE_MODEL", "google/gemma-4-E4B-it")
FP16 = "" if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else "--fp16"
os.environ["BASE_MODEL"], os.environ["FP16"] = BASE_MODEL, FP16
print(f"model {{BASE_MODEL}}   precision flag {{FP16 or '(bf16)'}}\\n")

# Tokenizer only, no weights, seconds. Confirms the delimiters and -- more
# importantly -- whether the template opens the reasoning block itself.
subprocess.run([sys.executable, "scripts/inspect_chat_template.py",
                "--model", BASE_MODEL], cwd=PROJECT, check=False)

print("\\n" + "=" * 70 + "\\nbuilding data\\n" + "=" * 70)
for script in ("scripts/build_eval_set.py", "scripts/build_sample.py"):
    subprocess.run([sys.executable, script], cwd=PROJECT, check=True)
'''

PRELUDE = '''import os, torch
PROJECT = "{project}"
os.chdir(PROJECT)
BASE_MODEL = os.environ.setdefault("BASE_MODEL", "google/gemma-4-E4B-it")
# Turing (T4) and Pascal (P100) have no bfloat16. Detected, never asked.
FP16 = "" if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else "--fp16"
os.environ["FP16"] = FP16
'''

# --------------------------------------------------------------------------- 5
SMOKE = '''# CELL 5 — smoke test: 4 items, one per language. ~2 minutes.
# Catches a broken path here instead of an hour into the full run.
{prelude}
!cd {project} && python scripts/run_eval.py --mode baseline \\
    --base $BASE_MODEL --out results_smoke --limit 1 $FP16

print("\\nCheck three things above before continuing:")
print("  1. 'architecture: gemma4' appeared before any download")
print("  2. format is 100% — the think block parsed")
print("  3. the reasoning is actually in the requested language")
'''

# --------------------------------------------------------------------------- 6
BASELINE = '''# CELL 6 — THE BASELINE. 48 items, untouched base model. 20-60 minutes.
# This is the "before" the whole project is measured against.
import os
PROJECT = "{project}"
os.chdir(PROJECT)

!cd {project} && python scripts/run_eval.py --mode baseline \\
    --base $BASE_MODEL --out results $FP16
'''

BASELINE_TABLE = '''# CELL 7 — the baseline table. Keep this; it is what the fine-tune must beat.
PROJECT = "{project}"
print(open(f"{{PROJECT}}/results/baseline/baseline_table.txt").read())
'''

# --------------------------------------------------------------------------- 8
TRAIN_MD = """## 8. Fine-tune with QLoRA

Base frozen in 4-bit, adapters trained on top. LoRA targets are discovered from
the loaded model rather than hardcoded, so this still works if Gemma 4 names its
projections differently from earlier releases.

`--allow-unverified` is here because the Wolof native review has not happened
yet. It stamps the model card as a pipeline test. **Remove it once the review is
signed off**, and the resulting numbers become reportable."""

TRAIN = '''# CELL 8 — QLoRA fine-tune. 15-40 minutes for 80 rows.
import os
PROJECT = "{project}"
os.chdir(PROJECT)

!cd {project} && python scripts/train_lora.py \\
    --data data/sample20/sample20.jsonl \\
    --base $BASE_MODEL --out artifacts/adapter \\
    --epochs 3 --lora-r 16 --allow-unverified $FP16
'''

# --------------------------------------------------------------------------- 9
COMPARE = '''# CELL 9 — evaluate the fine-tune on the SAME held-out set, and compare.
{prelude}import json

!cd {project} && python scripts/run_eval.py --mode adapter \\
    --base $BASE_MODEL --adapter artifacts/adapter --out results $FP16

base  = json.load(open(f"{{PROJECT}}/results/baseline/baseline_report.json"))["summary"]
tuned = json.load(open(f"{{PROJECT}}/results/finetuned/baseline_report.json"))["summary"]
card  = json.load(open(f"{{PROJECT}}/artifacts/adapter/model_card.json"))

METRICS = ("reasoning_correct", "reasoning_lang_ok", "answer_lang_ok",
           "collapse_to_english", "correct_and_in_language")
deltas = {{lang: {{m: round(tuned["by_language"][lang][m] - base["by_language"][lang][m], 4)
                 for m in METRICS}}
          for lang in base["by_language"]}}

json.dump({{"base_model": os.environ["BASE_MODEL"], "adapter": "artifacts/adapter",
           "model_card": card, "baseline": base, "finetuned": tuned, "deltas": deltas}},
          open(f"{{PROJECT}}/results/comparison.json", "w"), indent=2, ensure_ascii=False)

print(f"\\n{{'lang':>5}}  {{'correct':>9}} {{'in-language':>12}} {{'collapse-EN':>12}}")
for lang, d in deltas.items():
    print(f"{{lang:>5}}  {{d['reasoning_correct']:>+9.0%}} "
          f"{{d['correct_and_in_language']:>+12.0%}} {{d['collapse_to_english']:>+12.0%}}")
print("\\nFor collapse-to-English, negative is the improvement.")
'''

# -------------------------------------------------------------------------- 10
EXPORT = '''# CELL 10 — export for the web app, and persist everything.
{prelude}import shutil, pathlib, subprocess, sys

subprocess.run([sys.executable, "scripts/export_model.py",
                "--adapter", "artifacts/adapter", "--base", os.environ["BASE_MODEL"],
                "--out", "artifacts/serve", "--kind", "adapter"], cwd=PROJECT, check=True)

dest = pathlib.Path("{save_dir}")
dest.mkdir(parents=True, exist_ok=True)
for name in ("artifacts/serve", "results"):
    shutil.copytree(f"{{PROJECT}}/{{name}}", dest / pathlib.Path(name).name,
                    dirs_exist_ok=True)

print(f"saved to {{dest}}\\n")
for p in sorted(dest.rglob("*")):
    if p.is_file():
        print(f"  {{p.relative_to(dest)}}  ({{p.stat().st_size/1e6:.1f}} MB)")
print("\\n{save_note}")
'''


def build(platform: str, cfg: dict, path: Path) -> None:
    def sub(text: str) -> str:
        """Fill the placeholders, then un-double the braces.

        The templates double their braces so that f-strings and dict literals
        survive; those must be collapsed back afterwards, or the notebook ships
        code like f"{{ROOT}}/repo" -- which is not a crash but is worse: it
        silently resolves to a directory literally named "{ROOT}".
        """
        text = text.replace("{prelude}", PRELUDE)
        for key, value in (("{project}", cfg["project"]), ("{root}", cfg["root"]),
                           ("{branch}", BRANCH), ("{repo}", REPO),
                           ("{auth}", cfg["auth"]), ("{accel_hint}", cfg["accel_hint"]),
                           ("{save_dir}", cfg["save_dir"]),
                           ("{save_note}", cfg["save_note"])):
            text = text.replace(key, value)
        return text.replace("{{", "{").replace("}}", "}")

    cells = [
        ("md", INTRO.format(platform=platform, accel=cfg["accel"],
                            net=cfg["net"], secrets=cfg["secrets"])),
        ("md", "## 2. Environment\n\nInstalls dependencies and checks the GPU. "
               "**This cell may restart the session** — if it does, run it again."),
        ("code", sub(ENV)),
        ("md", "## 3. Code and credentials\n\nClones fresh every run, then runs "
               "the test suite. If the tests fail, stop: every later number "
               "would be meaningless."),
        ("code", sub(SETUP)),
        ("md", "## 4. Thinking format, then data\n\nConfirms how this model marks "
               "its reasoning block, then builds the 48-item held-out set and the "
               "20-example sample."),
        ("code", sub(FORMAT_AND_DATA)),
        ("md", "## 5. Smoke test\n\nFour items, one per language."),
        ("code", sub(SMOKE)),
        ("md", "## 6. Baseline — the measurement everything else is judged against"),
        ("code", sub(BASELINE)),
        ("code", sub(BASELINE_TABLE)),
        ("md", TRAIN_MD),
        ("code", sub(TRAIN)),
        ("md", "## 9. Evaluate and compare"),
        ("code", sub(COMPARE)),
        ("md", "## 10. Export and save"),
        ("code", sub(EXPORT)),
    ]

    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(s) if t == "md" else nbf.v4.new_code_cell(s)
                for t, s in cells]
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "accelerator": "GPU",
    }
    nbf.validate(nb)
    path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, str(path))
    print(f"wrote {path}  ({len(nb.cells)} cells)")


KAGGLE = {
    "root": "/kaggle/working",
    "project": "/kaggle/working/repo/mlr",
    "accel": "Settings → Accelerator → **GPU T4 x2** (or P100)",
    "net": "Settings → **Internet: On** — the model download needs it",
    "secrets": "**Add-ons → Secrets**",
    "accel_hint": "Settings > Accelerator",
    "auth": '''from kaggle_secrets import UserSecretsClient
try:
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
    print("HF token loaded")
except Exception as exc:
    print(f"NO HF TOKEN ({exc}) — add it under Add-ons > Secrets, "
          f"and accept the Gemma 4 licence on its model page.")''',
    "save_dir": "/kaggle/working/gemma4-mlr",
    "save_note": "Everything under /kaggle/working is kept when the notebook "
                 "commits, and can be attached to another notebook or downloaded.",
}

COLAB = {
    "root": "/content",
    "project": "/content/repo/mlr",
    "accel": "Runtime → Change runtime type → **T4 GPU** or better",
    "net": "Colab has internet by default — nothing to do",
    "secrets": "the **key icon** in the left sidebar (enable notebook access)",
    "accel_hint": "Runtime > Change runtime type",
    "auth": '''from google.colab import userdata
try:
    os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
    print("HF token loaded")
except Exception as exc:
    print(f"NO HF TOKEN ({exc}) — add it via the key icon in the sidebar, "
          f"and accept the Gemma 4 licence on its model page.")''',
    "save_dir": "/content/drive/MyDrive/gemma4-mlr",
    "save_note": "Mount Drive first (from google.colab import drive; "
                 "drive.mount('/content/drive')) or this saves to the "
                 "ephemeral runtime only.",
}


def main() -> int:
    build("Kaggle", KAGGLE, OUT / "kaggle_gemma4_multilingual_reasoning.ipynb")
    build("Colab", COLAB, OUT / "colab_gemma4_multilingual_reasoning.ipynb")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
