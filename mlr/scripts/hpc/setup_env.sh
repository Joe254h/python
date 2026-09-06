#!/bin/bash
# One-time environment setup for HPC. Run on a LOGIN node (compute nodes are
# usually offline), then submit with: sbatch scripts/hpc/train.slurm
set -euo pipefail

cd "$(dirname "$0")/../.."

module load cuda/12.4 2>/dev/null || true
module load python/3.11 2>/dev/null || true

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Match the CUDA build to your cluster's driver.
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install "transformers>=4.57" "peft>=0.14" "accelerate>=1.0" \
            "bitsandbytes>=0.44" "datasets>=3.0"

# Gemma 4 is gated: accept the licence on the model page, then authenticate.
# Prefer an env var over `huggingface-cli login` in shared filesystems.
if [[ -n "${HF_TOKEN:-}" ]]; then
    export HF_HOME="${HF_HOME:-$PWD/.hf_cache}"
    python - <<'PY'
import os
from huggingface_hub import snapshot_download
model = os.environ.get("BASE_MODEL", "google/gemma-4-E4B-it")
print(f"staging {model} into {os.environ['HF_HOME']} ...")
snapshot_download(model, token=os.environ["HF_TOKEN"])
print("done -- compute nodes can now run with HF_HUB_OFFLINE=1")
PY
else
    echo "HF_TOKEN not set: skipping model staging."
    echo "Export HF_TOKEN and re-run to pre-download weights for offline nodes."
fi

python3 -m unittest discover -s tests
echo "environment ready."
