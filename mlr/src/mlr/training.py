"""QLoRA fine-tuning, shared by the Colab notebook, the Kaggle notebook and HPC.

Protocol item 4: freeze the base, train adapters only. One method, done well.

Heavy imports (torch, transformers, peft) happen inside functions on purpose,
so this module can be imported -- and its configuration and data path tested --
on a machine with none of them installed. That is how the pipeline gets checked
without a GPU.

Every run writes a model card recording the base model, the data fingerprint,
the hyperparameters, and whether unverified data was used. A saved adapter with
no provenance is not a result.
"""

from __future__ import annotations

import json
import platform
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Sequence

from .data import Corpus
from .format_guard import GEMMA4_THINKING


@dataclass
class LoraSettings:
    """Defaults chosen for a ~250-example set on a single 16 GB GPU.

    Rank 16 is deliberate: with a few hundred examples a larger adapter mostly
    memorises. If the corpus grows past a couple of thousand rows, raise `r`
    before reaching for a bigger base model.
    """

    r: int = 16
    alpha: int = 32
    dropout: float = 0.05
    # Left empty so targets are DISCOVERED from the loaded model rather than
    # guessed. Gemma 4's exact module names could not be verified offline, and
    # a wrong hardcoded list silently trains far fewer parameters than intended.
    target_modules: tuple[str, ...] = ()
    bias: str = "none"


@dataclass
class TrainSettings:
    base_model: str = "google/gemma-4-E4B-it"
    output_dir: str = "artifacts/adapter"
    epochs: float = 3.0
    lr: float = 2e-4
    batch_size: int = 1
    grad_accum: int = 8
    max_seq_len: int = 1024
    warmup_ratio: float = 0.03
    seed: int = 0
    load_in_4bit: bool = True           # QLoRA; set False for plain LoRA on big GPUs
    bf16: bool = True
    gradient_checkpointing: bool = True
    logging_steps: int = 5
    save_total_limit: int = 1
    lora: LoraSettings = field(default_factory=LoraSettings)


def discover_lora_targets(model) -> list[str]:
    """Find the attention/MLP projection names actually present in the model.

    Safer than a hardcoded list: if Gemma 4 names its projections differently
    from earlier Gemma releases, this still targets the right modules instead
    of quietly training almost nothing.
    """
    import torch.nn as nn

    try:
        from bitsandbytes.nn import Linear4bit
        linear_types = (nn.Linear, Linear4bit)
    except ImportError:
        linear_types = (nn.Linear,)

    names = set()
    for full_name, module in model.named_modules():
        if isinstance(module, linear_types):
            leaf = full_name.split(".")[-1]
            # The LM head is deliberately excluded: adapting it destabilises
            # training and inflates the adapter for no benefit.
            if leaf not in ("lm_head", "score", "classifier"):
                names.add(leaf)
    return sorted(names)


def build_model_and_tokenizer(cfg: TrainSettings):
    """Load the base model 4-bit and attach a LoRA adapter."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Fail now if the think-block delimiters are wrong, not after an hour of
    # training that produces unparseable output.
    GEMMA4_THINKING.resolve_from_tokenizer(tokenizer)

    kwargs = {"dtype": torch.bfloat16 if cfg.bf16 else torch.float16,
              "device_map": "auto"}
    if cfg.load_in_4bit:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if cfg.bf16 else torch.float16,
        )

    model = AutoModelForCausalLM.from_pretrained(cfg.base_model, **kwargs)

    if cfg.load_in_4bit:
        model = prepare_model_for_kbit_training(
            model, use_gradient_checkpointing=cfg.gradient_checkpointing)

    targets = list(cfg.lora.target_modules) or discover_lora_targets(model)
    print(f"LoRA target modules: {targets}")

    model = get_peft_model(model, LoraConfig(
        r=cfg.lora.r,
        lora_alpha=cfg.lora.alpha,
        lora_dropout=cfg.lora.dropout,
        bias=cfg.lora.bias,
        target_modules=targets,
        task_type="CAUSAL_LM",
    ))
    model.print_trainable_parameters()
    return model, tokenizer, targets


def build_dataset(corpus_rows: Sequence[dict], tokenizer, cfg: TrainSettings):
    """Tokenize with the loss masked to the assistant turn only.

    Training on the prompt tokens as well would spend capacity learning to
    reproduce questions. We want the reasoning and the answer.
    """
    from torch.utils.data import Dataset

    class ReasoningDataset(Dataset):
        def __init__(self, rows):
            self.rows = list(rows)

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, i):
            row = self.rows[i]
            prompt_msgs = []
            if row["system"]:
                prompt_msgs.append({"role": "system", "content": row["system"]})
            prompt_msgs.append({"role": "user", "content": row["user"]})

            prompt = tokenizer.apply_chat_template(
                prompt_msgs, tokenize=False, add_generation_prompt=True,
                enable_thinking=True,
            )
            full = prompt + row["target"] + (tokenizer.eos_token or "")

            enc = tokenizer(full, truncation=True, max_length=cfg.max_seq_len)
            prompt_len = len(tokenizer(prompt, truncation=True,
                                       max_length=cfg.max_seq_len)["input_ids"])

            labels = list(enc["input_ids"])
            for j in range(min(prompt_len, len(labels))):
                labels[j] = -100          # mask the prompt out of the loss
            enc["labels"] = labels
            return enc

    return ReasoningDataset(corpus_rows)


def train(corpus: Corpus, cfg: TrainSettings) -> dict:
    """Run the fine-tune and save adapter, tokenizer and model card."""
    from transformers import (DataCollatorForSeq2Seq, Trainer, TrainingArguments,
                              set_seed)

    set_seed(cfg.seed)
    out = Path(cfg.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    model, tokenizer, targets = build_model_and_tokenizer(cfg)
    train_ds = build_dataset(corpus.train, tokenizer, cfg)
    val_ds = build_dataset(corpus.val, tokenizer, cfg) if corpus.val else None

    args = TrainingArguments(
        output_dir=str(out / "checkpoints"),
        num_train_epochs=cfg.epochs,
        per_device_train_batch_size=cfg.batch_size,
        gradient_accumulation_steps=cfg.grad_accum,
        learning_rate=cfg.lr,
        warmup_ratio=cfg.warmup_ratio,
        logging_steps=cfg.logging_steps,
        save_total_limit=cfg.save_total_limit,
        bf16=cfg.bf16,
        gradient_checkpointing=cfg.gradient_checkpointing,
        report_to=[],
        eval_strategy="epoch" if val_ds else "no",
        save_strategy="epoch",
        seed=cfg.seed,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model, args=args,
        train_dataset=train_ds, eval_dataset=val_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True,
                                             label_pad_token_id=-100),
    )
    started = time.time()
    result = trainer.train()
    elapsed = round(time.time() - started, 1)

    model.save_pretrained(str(out))
    tokenizer.save_pretrained(str(out))

    card = build_model_card(cfg, corpus, targets, elapsed,
                            float(result.training_loss))
    (out / "model_card.json").write_text(
        json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nadapter + tokenizer + model card -> {out}")
    return card


def build_model_card(cfg: TrainSettings, corpus: Corpus, targets, elapsed, loss) -> dict:
    """Provenance for the saved adapter. The web app reads and displays this."""
    return {
        "base_model": cfg.base_model,
        "method": "QLoRA (4-bit base, LoRA adapters)" if cfg.load_in_4bit else "LoRA",
        "languages": ["en", "fr", "sw", "wo"],
        "thinking_format": {
            "open": GEMMA4_THINKING.open_token,
            "close": GEMMA4_THINKING.close_token,
        },
        "data": {
            "fingerprint": corpus.fingerprint,
            "train_rows": len(corpus.train),
            "val_rows": len(corpus.val),
            "composition": corpus.composition,
            "trained_on_unverified_data": corpus.allow_unverified,
            "unverified_languages": corpus.unverified_langs,
            "notes": corpus.notes,
        },
        "hyperparameters": {
            **{k: v for k, v in asdict(cfg).items() if k != "lora"},
            "lora": asdict(cfg.lora) | {"resolved_target_modules": list(targets)},
        },
        "training": {
            "final_loss": loss,
            "seconds": elapsed,
            "platform": platform.platform(),
        },
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evaluation": None,   # filled in by scripts/run_eval.py
        "caveat": (
            "A model trained with trained_on_unverified_data=true is a pipeline "
            "test, not a result. Do not report its numbers."
        ),
    }
