"""Free-tier LLM providers, rotated behind one interface.

The LLM does not decide anything in this system. It writes report prose,
adjudicates borderline paraphrase matches, and generates training data for the
classifier. Those are generation tasks, which is what these models are for --
the verdict comes from retrieval and a calibrated classifier, neither of which
calls anything here.

The design problem is that no single free tier is large enough. Groq allows
1,000 requests a day, OpenRouter's free models 50, Google AI Studio runs at
10-15 requests a minute. Rotating across four of them, caching every response
on disk, and refusing to exceed a declared daily budget turns those into a
workable allowance. `Router` is that policy; the provider classes are thin.

Shape follows `mlr/src/mlr/backends.py`: a Protocol, several real backends and
a mock that lets everything downstream be exercised with no network at all.
Only the standard library is used, so a worker needs no extra dependency to
call any of these.

Free-tier numbers move constantly. The ones in the docstrings are a
September 2026 snapshot; `Router` enforces whatever budget it is given rather
than trusting them.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class ProviderError(RuntimeError):
    """A provider failed in a way the router should route around."""


class RateLimited(ProviderError):
    """A provider refused for quota reasons. Try the next one."""


class Provider(Protocol):
    name: str
    #: Requests permitted per day on the free tier, as configured.
    daily_budget: int

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        ...


# --------------------------------------------------------------------- HTTP


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 60) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        if exc.code in (429, 402, 403):
            raise RateLimited(f"{url} -> {exc.code}: {detail}") from exc
        raise ProviderError(f"{url} -> {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"{url} unreachable: {exc.reason}") from exc


@dataclass
class OpenAICompatible:
    """Every free tier worth using speaks the OpenAI chat-completions shape.

    Groq, Cerebras, OpenRouter and a local Ollama differ only in base URL,
    model id and where the key comes from, so one class covers all four.
    """

    name: str
    base_url: str
    model: str
    api_key_env: str
    daily_budget: int = 200
    timeout: int = 60

    @property
    def available(self) -> bool:
        return bool(os.environ.get(self.api_key_env)) or self.api_key_env == ""

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        key = os.environ.get(self.api_key_env, "")
        if self.api_key_env and not key:
            raise ProviderError(f"{self.name}: {self.api_key_env} is not set")

        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        data = _post_json(
            f"{self.base_url}/chat/completions",
            {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2,
            },
            headers,
            timeout=self.timeout,
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape") from exc


@dataclass
class GeminiProvider:
    """Google AI Studio. Different wire format, same job.

    Worth keeping despite the odd shape: the free tier carries a 1M-token
    context window, which is the only free way to put a whole thesis and its
    candidate sources in one prompt.
    """

    name: str = "gemini"
    model: str = "gemini-2.5-flash"
    api_key_env: str = "GEMINI_API_KEY"
    daily_budget: int = 1000
    timeout: int = 90

    @property
    def available(self) -> bool:
        return bool(os.environ.get(self.api_key_env))

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ProviderError(f"{self.name}: {self.api_key_env} is not set")

        payload: dict = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.2},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        data = _post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={key}",
            payload,
            {"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape") from exc


class MockProvider:
    """Scripted responses so the pipeline runs with no network and no keys.

    Not a toy, for the same reason `mlr`'s MockBackend is not: it is how the
    adjudication and report-writing paths get exercised in CI, where no free
    tier key exists and none should.
    """

    name = "mock"
    daily_budget = 10**9
    available = True

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        if "paraphrase" in prompt.lower() or "paraphrase" in system.lower():
            return json.dumps({"is_paraphrase": False, "confidence": 0.0,
                               "reason": "mock provider: no judgement made"})
        return "[mock provider] no language model was called for this report."


# ------------------------------------------------------------------- presets


def default_providers() -> list[Provider]:
    """Every free tier we know how to talk to, best daily volume first.

    Cerebras leads on volume (1M tokens/day), Groq on latency (~320 tok/s on
    Llama 3.3 70B), Gemini on context, OpenRouter on breadth of fallback.
    Ollama is last because it is only there when someone is running it.
    """
    return [
        OpenAICompatible(
            name="cerebras",
            base_url="https://api.cerebras.ai/v1",
            model="llama-3.3-70b",
            api_key_env="CEREBRAS_API_KEY",
            daily_budget=800,
        ),
        OpenAICompatible(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            model="llama-3.3-70b-versatile",
            api_key_env="GROQ_API_KEY",
            daily_budget=900,
        ),
        GeminiProvider(),
        OpenAICompatible(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            model="deepseek/deepseek-chat-v3:free",
            api_key_env="OPENROUTER_API_KEY",
            daily_budget=45,
        ),
        OpenAICompatible(
            name="ollama",
            base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434/v1"),
            model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
            api_key_env="",
            daily_budget=10**6,
        ),
    ]


# -------------------------------------------------------------------- router


@dataclass
class Router:
    """Rotates across providers, caches on disk, and stops at a budget.

    Failover is on `RateLimited` and `ProviderError` alike: a free tier that is
    down is indistinguishable from one that is exhausted, and the correct
    response to both is the next provider. When every provider is spent the
    router raises rather than silently degrading, because a report that
    quietly lost its explanatory text should look like a failure.
    """

    providers: list[Provider] = field(default_factory=default_providers)
    cache_dir: Path | None = None
    #: Hard ceiling across all providers for one day, regardless of their own.
    daily_budget: int = 500
    _spent: dict[str, int] = field(default_factory=dict, init=False)
    _day: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.cache_dir is not None:
            self.cache_dir = Path(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- budgeting

    def _roll_day(self) -> None:
        today = time.strftime("%Y-%m-%d")
        if today != self._day:
            self._day = today
            self._spent = {}

    @property
    def spent_today(self) -> int:
        self._roll_day()
        return sum(self._spent.values())

    def usage(self) -> dict[str, int]:
        self._roll_day()
        return dict(self._spent)

    # ----------------------------------------------------------------- cache

    def _cache_path(self, key: str) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"{key}.json"

    @staticmethod
    def _key(prompt: str, system: str, max_tokens: int) -> str:
        blob = f"{system}\x00{prompt}\x00{max_tokens}".encode("utf-8")
        return hashlib.blake2b(blob, digest_size=16).hexdigest()

    # ------------------------------------------------------------------ call

    def complete(
        self, prompt: str, system: str = "", max_tokens: int = 512
    ) -> tuple[str, str]:
        """Return `(text, provider_name)`. Cached hits report provider "cache"."""
        self._roll_day()
        key = self._key(prompt, system, max_tokens)

        path = self._cache_path(key)
        if path is not None and path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["text"], "cache"

        if self.spent_today >= self.daily_budget:
            raise RateLimited(
                f"router daily budget of {self.daily_budget} requests is spent"
            )

        errors: list[str] = []
        for provider in self.providers:
            if not getattr(provider, "available", True):
                continue
            if self._spent.get(provider.name, 0) >= provider.daily_budget:
                errors.append(f"{provider.name}: own budget spent")
                continue
            try:
                text = provider.complete(prompt, system=system, max_tokens=max_tokens)
            except ProviderError as exc:
                errors.append(f"{provider.name}: {exc}")
                continue

            self._spent[provider.name] = self._spent.get(provider.name, 0) + 1
            if path is not None:
                path.write_text(
                    json.dumps({"text": text, "provider": provider.name}),
                    encoding="utf-8",
                )
            return text, provider.name

        raise ProviderError("every provider failed:\n  " + "\n  ".join(errors))


def mock_router() -> Router:
    """A router that never touches the network. The CI default."""
    return Router(providers=[MockProvider()], daily_budget=10**9)
