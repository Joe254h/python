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
        # Resolve the thinking delimiters from the tokenizer itself. The
        # configured constants are only a starting guess; the tokenizer is the
        # authority, and this replaces them with what it actually reports.
        self.fmt = self.fmt.resolve_from_tokenizer(self.tokenizer)
        print(f"thinking format: open={self.fmt.open_token!r} "
              f"close={self.fmt.close_token!r} "
              f"opened_by_template={self.fmt.open_emitted_by_template}")

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
    fmt: ThinkingFormat = GEMMA4_THINKING
    name: str = "llama.cpp"
    # Gemma 4 control tokens, confirmed against a real tokenizer dump.
    bos: str = "<bos>"
    turn_open: str = "<|turn>"
    turn_close: str = "<turn|>"
    think_token: str = "<|think|>"
    stop: tuple = ("<turn|>", "<eos>")

    def __post_init__(self) -> None:
        from llama_cpp import Llama  # noqa

        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            verbose=False,
        )

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        # NOT create_chat_completion. Gemma 4 switches thinking on with a
        # <|think|> control token that its chat template injects into the first
        # system turn when enable_thinking=True -- and llama.cpp's chat
        # completion API has no way to pass that flag. Going through it would
        # silently produce a NON-thinking model, and the whole project is about
        # the thinking. So the prompt is rendered here instead.
        prompt = self.render_prompt(system, user)
        out = self.llm.create_completion(
            prompt=prompt,
            max_tokens=max_new_tokens,
            temperature=0.0,
            stop=list(self.stop),
        )
        return out["choices"][0]["text"]

    def render_prompt(self, system: str, user: str) -> str:
        """Gemma 4's prompt format, with thinking switched on.

        Taken from a real tokenizer dump, which renders a thinking-enabled
        prompt as:

            <bos><|turn>system\n<|think|>\n<turn|>\n
            <|turn>user\n...<turn|>\n<|turn>model\n

        The probe that produced it had empty system content, so the exact
        placement of a non-empty system message is inferred. Protocol item 6
        requires confirming the thinking mode still works after quantization --
        run the held-out evaluation against the GGUF and check `format_ok`. If
        the think block stops parsing, this template is where to look first.
        """
        return (
            f"{self.bos}{self.turn_open}system\n{self.think_token}\n{system}"
            f"{self.turn_close}\n{self.turn_open}user\n{user}"
            f"{self.turn_close}\n{self.turn_open}model\n"
        )


@dataclass
class MockBackend:
    """Replays canned outputs keyed by (lang, question-prefix).

    Used to prove the harness catches what it claims to catch. Any prompt with
    no scripted reply raises, so a silent gap in a test cannot pass as a pass.
    """

    script: dict[str, str]
    fmt: ThinkingFormat = GEMMA4_THINKING
    name: str = "mock"

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        for key, reply in self.script.items():
            if key in user:
                return reply
        raise KeyError(f"MockBackend has no scripted reply for: {user[:80]!r}")
