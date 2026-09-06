#!/usr/bin/env python3
"""Turn a trained adapter into something the web application can serve.

Three output shapes, because the serving hardware decides which you want:

  adapter  (default)  ~50-200 MB. Base model loaded at serve time, adapter
                      applied on top. Small enough for git, and the only
                      artifact you should commit.
  merged              Full fp16 weights, ~9 GB for E4B. Faster to load, needs
                      a GPU. Never commit this.
  gguf                Quantized for CPU serving via llama.cpp. This is also
                      the phase-two on-device path.

Always writes serve_manifest.json, which is the contract the web app reads:
it names the artifact kind, the paths, the thinking delimiters and the data
fingerprint, so the app can display what it is actually serving.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mlr.format_guard import GEMMA4_THINKING     # noqa: E402


def write_manifest(out: Path, kind: str, base: str, adapter: Path,
                   merged: Path | None, gguf: Path | None) -> dict:
    card_path = adapter / "model_card.json"
    card = json.loads(card_path.read_text(encoding="utf-8")) if card_path.exists() else {}
    manifest = {
        "kind": kind,
        "base_model": base,
        "adapter_path": str(adapter) if adapter.exists() else None,
        "merged_path": str(merged) if merged else None,
        "gguf_path": str(gguf) if gguf else None,
        "languages": ["en", "fr", "sw", "wo"],
        "thinking_format": {
            "open": GEMMA4_THINKING.open_token,
            "close": GEMMA4_THINKING.close_token,
        },
        "data_fingerprint": card.get("data", {}).get("fingerprint"),
        "trained_on_unverified_data": card.get("data", {}).get(
            "trained_on_unverified_data", True),
        "model_card": card or None,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "serve_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def merge_adapter(base: str, adapter: Path, dest: Path) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(f"loading base {base} in bf16 ...")
    model = AutoModelForCausalLM.from_pretrained(
        base, dtype=torch.bfloat16, device_map="cpu")
    print(f"applying adapter {adapter} ...")
    model = PeftModel.from_pretrained(model, str(adapter))
    print("merging ...")
    model = model.merge_and_unload()
    dest.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(dest), safe_serialization=True)
    AutoTokenizer.from_pretrained(base).save_pretrained(str(dest))
    print(f"merged model -> {dest}")


GGUF_HELP = """
GGUF export needs llama.cpp's converter, which is a separate checkout:

    git clone https://github.com/ggml-org/llama.cpp
    pip install -r llama.cpp/requirements.txt
    python llama.cpp/convert_hf_to_gguf.py {merged} \\
        --outfile {gguf}/gemma4-mlr-f16.gguf --outtype f16
    llama.cpp/build/bin/llama-quantize \\
        {gguf}/gemma4-mlr-f16.gguf {gguf}/gemma4-mlr-Q4_K_M.gguf Q4_K_M

Then serve with:  python webapp/server.py --gguf {gguf}/gemma4-mlr-Q4_K_M.gguf

After quantizing, re-run the held-out evaluation against the GGUF. Protocol
item 6 requires confirming the thinking mode still works after quantization,
and that check is exactly `format_ok` in the report -- if the think block stops
parsing, quantization broke it.
"""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Export a trained adapter for serving.")
    p.add_argument("--adapter", default="artifacts/adapter")
    p.add_argument("--base", default="google/gemma-4-E4B-it")
    p.add_argument("--out", default="artifacts/serve")
    p.add_argument("--kind", choices=("adapter", "merged", "gguf"), default="adapter")
    args = p.parse_args(argv)

    adapter, out = Path(args.adapter), Path(args.out)
    if not adapter.exists():
        print(f"adapter not found: {adapter}\nRun scripts/train_lora.py first.",
              file=sys.stderr)
        return 2

    merged = gguf = None
    if args.kind in ("merged", "gguf"):
        merged = out / "merged"
        merge_adapter(args.base, adapter, merged)
    if args.kind == "gguf":
        gguf = out / "gguf"
        gguf.mkdir(parents=True, exist_ok=True)
        print(GGUF_HELP.format(merged=merged, gguf=gguf))

    if args.kind == "adapter":
        dest = out / "adapter"
        if dest.resolve() != adapter.resolve():
            shutil.copytree(adapter, dest, dirs_exist_ok=True)
        adapter = dest

    manifest = write_manifest(out, args.kind, args.base, adapter, merged, gguf)
    print(f"\nserve manifest -> {out/'serve_manifest.json'}")
    if manifest["trained_on_unverified_data"]:
        print("\n*** artifact trained on UNVERIFIED data -- the web app will "
              "display this prominently. ***")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
