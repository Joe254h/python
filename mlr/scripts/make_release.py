#!/usr/bin/env python3
"""Package the project into zip bundles.

One complete archive plus four focused ones, because the people who need this
project need different parts of it: the Wolof reviewer does not need Python,
and someone uploading to Colab does not need the SLURM job.

    python scripts/make_release.py            # writes to dist/

Every bundle gets a generated README naming what it is and what to do with it,
so an archive that arrives on its own still explains itself.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
STEM = "gemma4-multilingual-reasoning"

# Never packaged: caches, virtualenvs, model weights, and run outputs.
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", ".hf_cache", "artifacts",
                "logs", "dist", ".ipynb_checkpoints", "selftest"}
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".zip"}
EXCLUDE_NAMES = {"comparison.json", ".DS_Store"}

CORE = ["src/", "tests/", "requirements.txt", ".gitignore"]
DATA = ["data/"]
DOCS = ["docs/", "README.md"]
SCRIPTS = ["scripts/"]

BUNDLES: dict[str, dict] = {
    "complete": {
        "include": CORE + DATA + DOCS + SCRIPTS + ["notebooks/", "webapp/", "results/"],
        "blurb": """Everything: library, data, docs, notebooks, HPC job and web app.

Start here:

    python3 -m unittest discover -s tests     # 17 tests, standard library only
    python3 webapp/server.py --stub           # the interface, no model needed

Then pick a platform -- notebooks/ for Colab and Kaggle, scripts/hpc/ for a
cluster. All three call the same code in src/mlr/, so nothing drifts.

No number in this archive came from Gemma 4. See docs/BLOCKERS.md.""",
    },
    "notebooks": {
        "include": ["notebooks/"],
        "blurb": """The two notebooks, nothing else.

Upload one straight to Colab or Kaggle. Each one clones the rest of the project
itself on the first cell, so this is all you need to get going:

    colab_gemma4_multilingual_reasoning.ipynb   Runtime > Change runtime type > T4 GPU
    kaggle_gemma4_multilingual_reasoning.ipynb  Settings > GPU, and Internet: On

Gemma 4 is gated -- accept its licence, then add HF_TOKEN to Colab secrets or
Kaggle secrets before running.

Run the baseline (section 6) before training (section 7). A fine-tune with no
"before" proves nothing.""",
    },
    "hpc": {
        "include": CORE + DATA + SCRIPTS + ["docs/"],
        "blurb": """For a cluster. No notebooks, no web app.

    bash scripts/hpc/setup_env.sh     # on a LOGIN node: venv, deps, stage weights
    sbatch scripts/hpc/train.slurm    # then submit

setup_env.sh pre-downloads the model into .hf_cache so compute nodes can run
with HF_HUB_OFFLINE=1, which is what most clusters need.

Edit the module load lines in train.slurm to match your site. Nothing else in
it is site-specific.""",
    },
    "webapp": {
        "include": ["webapp/", "src/", "data/", "requirements.txt"],
        "blurb": """The web application and the code it imports.

    pip install fastapi uvicorn
    python webapp/server.py --stub    # interface only, no model, no GPU

To serve a real model, copy the adapter directory produced by training and:

    python webapp/server.py --manifest artifacts/serve/serve_manifest.json

The page shows the think block and the final answer as separate panels, each
with its own detected language, so language collapse is visible rather than
hidden by concatenation.""",
    },
    "review": {
        "include": ["docs/", "data/", "README.md"],
        "blurb": """For reviewers and collaborators who are not running any code.

No Python needed. The two files that matter:

    docs/WOLOF_REVIEW_PACKET.md   the native Wolof review -- start here.
                                  Blocking decision on French-in-Wolof is at the top.
    docs/SWAHILI_REVIEW.md        what was checked in Swahili and what was wrong

Also included: the held-out evaluation set, the 20-example sample with its
per-example provenance log, and the evaluation protocol.

Nothing in data/ is natively verified yet. That is what the packet is for.""",
    },
}


def wanted(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIX or path.name in EXCLUDE_NAMES:
        return False
    return path.is_file()


def collect(includes: list[str]) -> list[Path]:
    files: set[Path] = set()
    for inc in includes:
        target = ROOT / inc.rstrip("/")
        if inc.endswith("/") or target.is_dir():
            files.update(p for p in target.rglob("*") if wanted(p))
        elif target.is_file() and wanted(target):
            files.add(target)
    return sorted(files)


def readme_for(name: str, spec: dict, files: list[Path]) -> str:
    listing = "\n".join(f"  {p.relative_to(ROOT)}" for p in files[:400])
    more = "" if len(files) <= 400 else f"\n  ... and {len(files)-400} more"
    return f"""# Four-language reasoning on Gemma 4 -- "{name}" bundle

Swahili, Wolof, English and French reasoning on Gemma 4, keeping the model's
thinking rather than only its answers.

{spec['blurb']}

--------------------------------------------------------------------------
Data verification status: NOTHING is natively verified. Swahili is
model-checked, which is not human validation. Wolof is unreviewed machine
translation and must not be trained on or reported until a native speaker has
signed off (docs/WOLOF_REVIEW_PACKET.md).
--------------------------------------------------------------------------

{len(files)} files in this bundle:

{listing}{more}
"""


def build(name: str, spec: dict, out_dir: Path) -> Path:
    files = collect(spec["include"])
    if not files:
        raise SystemExit(f"bundle {name!r} matched no files")
    zip_path = out_dir / f"{STEM}-{name}.zip"
    top = f"{STEM}-{name}"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(f"{top}/README-BUNDLE.md", readme_for(name, spec, files))
        for f in files:
            z.write(f, f"{top}/{f.relative_to(ROOT)}")
    return zip_path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Package the project into zip bundles.")
    p.add_argument("--out", default=str(DIST))
    p.add_argument("--only", default="", help="comma-separated bundle names")
    args = p.parse_args(argv)

    out_dir = Path(args.out)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    names = args.only.split(",") if args.only else list(BUNDLES)
    rows = []
    for name in names:
        z = build(name, BUNDLES[name], out_dir)
        digest = hashlib.sha256(z.read_bytes()).hexdigest()[:16]
        with zipfile.ZipFile(z) as zf:
            n = len(zf.namelist())
        rows.append((z.name, n, z.stat().st_size, digest))

    width = max(len(r[0]) for r in rows)
    print(f"{'bundle':<{width}}  {'files':>6}  {'size':>9}  sha256")
    for name, n, size, digest in rows:
        print(f"{name:<{width}}  {n:>6}  {size/1024:>7.0f} KB  {digest}")
    (out_dir / "SHA256SUMS.txt").write_text(
        "\n".join(f"{d}  {n}" for n, _, _, d in rows) + "\n", encoding="utf-8")
    print(f"\n-> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
