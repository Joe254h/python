#!/bin/bash
#SBATCH --job-name=gemma4-mlr
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#
# QLoRA fine-tune of Gemma 4 for four-language reasoning.
#
#   sbatch scripts/hpc/train.slurm
#
# One 16 GB GPU is enough for E4B with 4-bit base. Adjust --gres, --partition
# and the module lines to match your cluster; nothing else here is site-specific.

set -euo pipefail

PROJECT_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
cd "$PROJECT_ROOT"
mkdir -p logs artifacts

echo "job $SLURM_JOB_ID on $(hostname)"
echo "started $(date -Is)"

# --- environment -----------------------------------------------------------
# Replace with your cluster's module names, or drop these lines if you manage
# the environment yourself.
module load cuda/12.4 2>/dev/null || echo "note: no cuda module, using system CUDA"
module load python/3.11 2>/dev/null || true

if [[ -d .venv ]]; then
    source .venv/bin/activate
else
    echo "no .venv found -- run scripts/hpc/setup_env.sh first" >&2
    exit 1
fi

# Compute nodes are usually offline. Stage the model to a shared cache from a
# login node first, then point HF_HOME at it and run fully offline.
export HF_HOME="${HF_HOME:-$PROJECT_ROOT/.hf_cache}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

# --- run -------------------------------------------------------------------
# Drop --allow-unverified once the Wolof native review is signed off; without
# the flag the job refuses to train on unverified rows, which is the point.
srun python scripts/train_lora.py \
    --data data/sample20/sample20.jsonl \
    --base "${BASE_MODEL:-google/gemma-4-E4B-it}" \
    --out "artifacts/adapter-${SLURM_JOB_ID}" \
    --epochs "${EPOCHS:-3}" \
    --lora-r "${LORA_R:-16}" \
    --allow-unverified

srun python scripts/run_eval.py \
    --mode compare \
    --base "${BASE_MODEL:-google/gemma-4-E4B-it}" \
    --adapter "artifacts/adapter-${SLURM_JOB_ID}" \
    --out "results/job-${SLURM_JOB_ID}"

srun python scripts/export_model.py \
    --adapter "artifacts/adapter-${SLURM_JOB_ID}" \
    --out "artifacts/serve" --kind adapter

echo "finished $(date -Is)"
