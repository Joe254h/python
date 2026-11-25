"""Report writing with a model on this computer, through Ollama. No API key, no credit.

Turned on with REPORT_WRITER=local in .env. It takes the same messages as the OpenRouter
writer. A long meeting does not fit a small model's working memory, so when the transcript is
too long it is first read in parts: the model takes notes on each part, keeping times, names,
decisions and owners, and the report is then written from those notes in one go.
"""

from __future__ import annotations

import hashlib
import os
import re

import requests

DEFAULT_LOCAL_MODEL = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"

_TRANSCRIPT = re.compile(r"(TRANSCRIPT \([^\n]*\)\n---\n)(.*)(\n---)\s*$", re.S)
_NOTES_HEADER = ("TRANSCRIPT NOTES (the recording was too long for the model on this computer to read at "
                 "once, so it was read in order, part by part, and these are the notes; times are mm:ss "
                 "from the start of the recording)\n---\n")
_NOTE_HEADINGS = (
    "PEOPLE: names and roles mentioned\n"
    "DISCUSSED: topics, arguments, figures and concerns, with who raised them when the transcript says\n"
    "DECIDED: what was agreed or approved, not what was only proposed\n"
    "ACTIONS: task - owner - deadline (\"Unassigned\" or \"Not set\" when the meeting did not say)\n"
    "OPEN: questions left unresolved and risks raised"
)


def _tokens(text: str) -> int:
    """A deliberately high estimate: about 3 characters per token, which covers Kiswahili."""
    return len(text) // 3 + 1


def split_parts(text: str, max_words: int) -> list[str]:
    """Pack whole transcript lines into parts of at most max_words words."""
    parts: list[str] = []
    current: list[str] = []
    count = 0
    for line in (ln.strip() for ln in text.splitlines()):
        if not line:
            continue
        words = line.split()
        while len(words) > max_words:  # one very long line
            if current:
                parts.append("\n".join(current))
                current, count = [], 0
            parts.append(" ".join(words[:max_words]))
            words = words[max_words:]
        if not words:
            continue
        if current and count + len(words) > max_words:
            parts.append("\n".join(current))
            current, count = [], 0
        current.append(" ".join(words))
        count += len(words)
    if current:
        parts.append("\n".join(current))
    return parts


def _find(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default


class LocalWriter:
    name = "on this computer"
    setup_hint = "open the Ollama app"

    def __init__(self):
        self.url = os.environ.get("OLLAMA_URL", "http://localhost:11434").strip().rstrip("/")
        self.model = os.environ.get("LOCAL_REPORT_MODEL", DEFAULT_LOCAL_MODEL).strip()
        # Ollama reserves memory for the whole window: 12k tokens is about 1.8 GB on top of the
        # 2.5 GB model. Every request uses the same size so Ollama never reloads the model.
        self.num_ctx = int(os.environ.get("LOCAL_REPORT_CONTEXT", "12288"))
        self.part_words = int(os.environ.get("LOCAL_PART_WORDS", "1800"))
        self.max_tokens = int(os.environ.get("LOCAL_REPORT_MAX_TOKENS", "4000"))
        self.timeout = int(os.environ.get("LOCAL_REPORT_TIMEOUT", "1800"))
        self.on_progress = None  # set by the processor to show "Reading part 2 of 6"
        self._notes: dict[str, str] = {}  # parts already read, so Retry report resumes

    @property
    def ready(self) -> bool:
        try:
            return requests.get(f"{self.url}/api/version", timeout=1).ok
        except requests.RequestException:
            return False

    def _pick(self, model: str | None) -> str:
        """Report settings may still hold an OpenRouter name such as google/gemini-2.5-pro.
        Those cannot run here, so use the local model instead."""
        model = (model or "").strip()
        if model and ("/" not in model or model.startswith("hf.co/")):
            return model
        return self.model

    def _say(self, stage: str) -> None:
        if self.on_progress:
            self.on_progress(stage)

    def chat(self, messages: list[dict], model: str, max_tokens: int) -> str:
        try:
            resp = requests.post(
                f"{self.url}/api/chat",
                json={"model": model, "messages": messages, "stream": False,
                      "options": {"num_ctx": self.num_ctx, "num_predict": max_tokens,
                                  "temperature": 0.2, "top_p": 0.8, "top_k": 20}},
                timeout=(10, self.timeout),
            )
        except requests.ConnectionError:
            raise RuntimeError("The report model on this computer is not running. Open the Ollama app, "
                               "then press Retry report.") from None
        except requests.Timeout:
            raise RuntimeError(f"The model on this computer took more than {self.timeout // 60} minutes on one "
                               "step. Close other programs and press Retry report, or set a smaller "
                               "LOCAL_PART_WORDS in .env.") from None
        if resp.status_code == 404 and "not found" in resp.text.lower():
            raise RuntimeError(f"Ollama does not have the model {model} yet. In PowerShell run: "
                               f"ollama pull {model} - then press Retry report.")
        if not resp.ok:
            raise RuntimeError(f"Ollama failed ({resp.status_code}): {resp.text[:300]}")
        body = resp.json()
        text = (body.get("message") or {}).get("content") or ""
        if body.get("done_reason") == "length":
            print(f"local_writer: {model} stopped at its output limit; the text may be cut short", flush=True)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("markdown").removeprefix("json").strip()
        return text

    def write(self, messages: list[dict], model: str | None = None) -> tuple[str, str]:
        model = self._pick(model)
        system, user = messages[0]["content"], messages[-1]["content"]
        m = _TRANSCRIPT.search(user)
        if m and _tokens(system + user) + self.max_tokens > self.num_ctx:
            notes = self._condense(m.group(2), system, user, model)
            user = user[:m.start()] + _NOTES_HEADER + notes + m.group(3)
            self._say("Writing the report from the notes")
        text = self.chat([*messages[:-1], {"role": messages[-1]["role"], "content": user}],
                         model, self.max_tokens)
        if not text:
            raise RuntimeError(f"{model} returned an empty report. Press Retry report.")
        return text, model

    def _condense(self, transcript: str, system: str, user: str, model: str) -> str:
        lang = _find(r"Write the entire report in ([^.\n]+)\.", system, "the language of the report")
        title = _find(r"Meeting title: ([^\n]+)", user, "the meeting")
        vocab = _find(r"VOCABULARY \(correct spellings\)\n([^\n]+)", user)
        parts = split_parts(transcript, self.part_words)
        notes = []
        for i, part in enumerate(parts, 1):
            key = hashlib.sha256(f"{model}|{lang}|{vocab}|{part}".encode()).hexdigest()
            if key not in self._notes:
                self._say(f"Writing the report: reading part {i} of {len(parts)}")
                self._notes[key] = self.chat([
                    {"role": "system", "content": (
                        "You take notes on one part of a meeting transcript for the secretary who will write "
                        "the report. Use only what this part says. Never invent names, numbers, dates, owners "
                        "or decisions. The transcript comes from speech recognition, may mix English and "
                        f"Kiswahili, and has misheard words; correct obvious errors. Write in {lang}.")},
                    {"role": "user", "content": (
                        f"Part {i} of {len(parts)} of the meeting \"{title}\".\n"
                        + (f"Correct spellings of names and terms: {vocab}\n" if vocab else "")
                        + "\nWrite short bullet notes under these headings. Put the [mm:ss] time from the "
                          "transcript after every decision and action. Write \"none\" under an empty heading.\n"
                        + _NOTE_HEADINGS
                        + f"\n\nTRANSCRIPT PART\n---\n{part}\n---")},
                ], model, 1000)
            notes.append(f"Part {i} of {len(parts)}\n{self._notes[key]}")

        # The notes must also fit, next to the instructions and template, in one request.
        fixed = _tokens(system) + _tokens(user) - _tokens(transcript) + _tokens(_NOTES_HEADER)
        budget = self.num_ctx - self.max_tokens - fixed
        while len(notes) > 1 and _tokens("\n\n".join(notes)) > budget:
            groups, group = [], []
            for note in notes:
                if len(group) >= 2 and _tokens("\n\n".join(group + [note])) > budget:
                    groups.append(group)
                    group = []
                group.append(note)
            groups.append(group)
            self._say(f"Writing the report: combining notes ({len(notes)} into {len(groups)})")
            notes = [g[0] if len(g) == 1 else self.chat([
                {"role": "system", "content": (
                    "You merge meeting notes. Keep every name, decision, action, owner, figure, date and "
                    f"[mm:ss] time exactly as written; drop only repetition. Write in {lang}.")},
                {"role": "user", "content": (
                    "Merge these notes from consecutive parts of the meeting into one set with the same "
                    f"headings:\n{_NOTE_HEADINGS}\n\n" + "\n\n".join(g))},
            ], model, 1500) for g in groups]
        return "\n\n".join(notes)
