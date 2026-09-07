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
    # "single" pins everything to GPU 0, which is what a 4-bit E4B wants.
    # "auto" shards across all visible GPUs -- only for a model that truly
    # does not fit, and it slows things down.
    device_map: str = "single"
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


def prepare_for_qlora(model, cfg: TrainSettings):
    """Memory-safe replacement for peft.prepare_model_for_kbit_training.

    peft's version upcasts every non-quantized parameter to float32. On this
    checkpoint that is fatal: bitsandbytes quantizes Linear layers only, so
    Gemma 4's embedding tables stay in bf16 -- about 5 GB of them -- and
    upcasting those is a single 10.5 GB allocation that does not fit on a T4
    alongside the 9.3 GB model.

    We are not training the embeddings. Only LoRA adapters get gradients, so
    the embeddings can stay in bf16. Only the 1-D parameters (layer norms) are
    upcast, which is where the numerical-stability argument actually applies
    and which costs a few MB rather than several GB.

    Everything else peft's helper does that matters for QLoRA -- freezing the
    base, gradient checkpointing, making inputs require grad so checkpointing
    works through a frozen embedding -- is done here explicitly.
    """
    import torch

    upcast_params = 0
    for _, param in model.named_parameters():
        param.requires_grad = False                 # base stays frozen
        if param.ndim == 1 and param.dtype in (torch.float16, torch.bfloat16):
            param.data = param.data.to(torch.float32)
            upcast_params += param.numel()

    if cfg.gradient_checkpointing:
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False})
        # Without this, checkpointing produces no gradient path back through a
        # frozen embedding layer and the adapters never learn anything.
        model.enable_input_require_grads()

    if hasattr(model, "config"):
        model.config.use_cache = False              # incompatible with checkpointing

    after = sum(torch.cuda.memory_allocated(i) for i in range(torch.cuda.device_count()))
    print(f"  upcast {upcast_params/1e6:.1f}M 1-D params (norms) to fp32; "
          f"embeddings left in bf16")
    print(f"  after prepare: {after/1e9:.2f} GB")
    return model


def report_load(model, cfg: TrainSettings) -> None:
    """Say what actually landed in memory, and refuse to continue if it is wrong.

    A quantization_config that silently fails to apply is the worst kind of
    bug: the model loads, training starts, and it dies later with an
    out-of-memory error that looks like the batch size is too big. The
    footprint is the evidence -- a 4-bit E4B is about 2 GB, a bf16 one about 9.
    Check it here, while the message can still name the cause.
    """
    import torch

    four_bit = sum(1 for m in model.modules()
                   if "4bit" in type(m).__name__.lower()
                   or "params4bit" in type(m).__name__.lower())
    total_gb = 0.0
    for i in range(torch.cuda.device_count()):
        gb = torch.cuda.memory_allocated(i) / 1e9
        total_gb += gb
        print(f"  GPU {i}: {gb:.2f} GB allocated")
    print(f"  4-bit modules: {four_bit}   total on GPU: {total_gb:.2f} GB")

    if cfg.load_in_4bit and four_bit == 0:
        raise RuntimeError(
            f"4-bit quantization did NOT take effect: no bitsandbytes 4-bit "
            f"modules are present ({total_gb:.1f} GB resident).\n\n"
            f"Note the expected footprint is not small: bitsandbytes quantizes "
            f"Linear layers only, so Gemma 4's embedding tables stay in bf16 "
            f"and a correctly-quantized load still sits around 9 GB.\n\n"
            f"Training would fail later with an out-of-memory error that looks "
            f"like a batch-size problem, so it stops here instead.\n\n"
            f"Check that bitsandbytes is installed and can see CUDA:\n"
            f"    python -c \"import bitsandbytes; print(bitsandbytes.__version__)\"\n"
            f"then reinstall it:  pip install -U bitsandbytes\n\n"
            f"Or train without quantization:  --no-4bit --max-seq-len 512\n"
            f"which skips the 4-bit path entirely (bf16 LoRA, ~9 GB)."
        )


def build_model_and_tokenizer(cfg: TrainSettings):
    """Load the base model 4-bit and attach a LoRA adapter."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Fail now if the think-block delimiters are wrong, not after an hour of
    # training that produces unparseable output.
    fmt = GEMMA4_THINKING.resolve_from_tokenizer(tokenizer)
    print(f"thinking format: open={fmt.open_token!r} close={fmt.close_token!r} "
          f"opened_by_template={fmt.open_emitted_by_template}")

    # A 4-bit E4B is ~2 GB and belongs on ONE GPU. device_map="auto" splits it
    # across every visible device, which buys nothing for a model this size and
    # makes the later fp32 upcast land on whichever GPU is already fullest.
    device_map = {"": 0} if cfg.device_map == "single" else cfg.device_map
    kwargs = {"dtype": torch.bfloat16 if cfg.bf16 else torch.float16,
              "device_map": device_map}
    if cfg.load_in_4bit:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if cfg.bf16 else torch.float16,
        )

    model = AutoModelForCausalLM.from_pretrained(cfg.base_model, **kwargs)
    report_load(model, cfg)

    if cfg.load_in_4bit:
        model = prepare_for_qlora(model, cfg)

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
    return model, tokenizer, targets, fmt


def build_dataset(corpus_rows: Sequence[dict], tokenizer, cfg: TrainSettings,
                  fmt=GEMMA4_THINKING):
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
            # Built here rather than taken from row["target"], so it matches
            # the format resolved from THIS tokenizer. If the template opens
            # the reasoning block, the target must not repeat the marker.
            target = fmt.training_target(row["thinking"], row["answer"])
            full = prompt + target + (tokenizer.eos_token or "")

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

    model, tokenizer, targets, fmt = build_model_and_tokenizer(cfg)
    train_ds = build_dataset(corpus.train, tokenizer, cfg, fmt)
    val_ds = build_dataset(corpus.val, tokenizer, cfg, fmt) if corpus.val else None

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
                            float(result.training_loss), fmt)
    (out / "model_card.json").write_text(
        json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nadapter + tokenizer + model card -> {out}")
    return card


def build_model_card(cfg: TrainSettings, corpus: Corpus, targets, elapsed, loss,
                     fmt=GEMMA4_THINKING) -> dict:
    """Provenance for the saved adapter. The web app reads and displays this."""
    return {
        "base_model": cfg.base_model,
        "method": "QLoRA (4-bit base, LoRA adapters)" if cfg.load_in_4bit else "LoRA",
        "languages": ["en", "fr", "sw", "wo"],
        "thinking_format": {
            "open": fmt.open_token,
            "close": fmt.close_token,
            "open_emitted_by_template": fmt.open_emitted_by_template,
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
