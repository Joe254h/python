"""Generation backends for the baseline run.

Three of them, because the constraint changes with the hardware:

  TransformersBackend  GPU, full precision or bitsandbytes 4-bit.
  LlamaCppBackend      CPU-only via a GGUF quant -- the realistic option on a
                       machine with no accelerator, and the same path the
                       phase-two on-device work will take.
  MockBackend          No model at all. Replays scripted outputs so the whole
                       harness -- parsing, scoring, aggregation -- can be
                       exercised and trusted before any weights exist.

MockBackend is not a toy. It is how we verify that the evaluation actually
detects the failures it claims to detect, which has to be settled before the
baseline numbers mean anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .format_guard import GEMMA4_THINKING, ThinkingFormat


class Backend(Protocol):
    name: str

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        ...


# Gemma 4 is a strong multilingual model, so the baseline must not hand it a
# crutch: the instruction to stay in the target language is stated once, the
# way a real user would, and never repeated or reinforced per-language.
LANG_NAME = {"en": "English", "fr": "French", "sw": "Swahili", "wo": "Wolof"}

BASELINE_SYSTEM = (
    "You are a careful reasoning assistant. Think step by step, then give a "
    "final answer. Reason in {language} and give your final answer in "
    "{language}."
)


def baseline_system_prompt(lang: str) -> str:
    return BASELINE_SYSTEM.format(language=LANG_NAME.get(lang, lang))


@dataclass
class TransformersBackend:
    """Gemma 4 through transformers. Requires accessible weights."""

    model_id: str = "google/gemma-4-E4B-it"
    device: str = "auto"
    load_in_4bit: bool = True
    fmt: ThinkingFormat = GEMMA4_THINKING
    name: str = "transformers"

    def __post_init__(self) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        # Fail loudly here if the thinking delimiters are wrong, rather than
        # silently producing a baseline that cannot be parsed.
        self.fmt.resolve_from_tokenizer(self.tokenizer)

        kwargs = {"device_map": self.device}
        if self.load_in_4bit:
            from transformers import BitsAndBytesConfig
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, **kwargs)

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True,          # keep the reasoning, do not suppress it
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,               # greedy: a baseline must be reproducible
        )
        return self.tokenizer.decode(
            out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=False
        )


@dataclass
class LlamaCppBackend:
    """Gemma 4 GGUF on CPU. The path that also serves phase-two on-device work."""

    model_path: str = ""
    n_ctx: int = 4096
    n_threads: int = 4
    name: str = "llama.cpp"

    def __post_init__(self) -> None:
        from llama_cpp import Llama  # noqa

        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            verbose=False,
        )

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        out = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_new_tokens,
            temperature=0.0,
        )
        return out["choices"][0]["message"]["content"]


@dataclass
class MockBackend:
    """Replays canned outputs keyed by (lang, question-prefix).

    Used to prove the harness catches what it claims to catch. Any prompt with
    no scripted reply raises, so a silent gap in a test cannot pass as a pass.
    """

    script: dict[str, str]
    name: str = "mock"

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        for key, reply in self.script.items():
            if key in user:
                return reply
        raise KeyError(f"MockBackend has no scripted reply for: {user[:80]!r}")
