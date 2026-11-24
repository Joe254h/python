#!/usr/bin/env python3
"""Write a meeting report from a saved transcript with a model on this computer.

No API key and no credits: the model runs in Ollama (default) or any
OpenAI-compatible local server (llama.cpp's llama-server, LM Studio).

Long meetings are summarised section by section, then combined, so an
87-minute transcript fits a 4B model's working memory on a 12 GB laptop.
Finished sections are saved as they complete; if a run stops, the next run
picks up where it left off.

    python local_report.py --check
    python local_report.py transcript.txt --title "Day 5 RCC Morning session"
    python local_report.py transcript.json --language sw --report-language en

Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DEFAULT_MODEL = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"
DEFAULT_URL = "http://localhost:11434"

LANG_NAMES = {"en": "English", "sw": "Kiswahili"}

HEADINGS = {
    "en": {
        "summary": "Summary",
        "decisions": "Decisions",
        "actions": "Action items",
        "discussion": "Discussion by topic",
        "open": "Open questions",
        "task": "Task",
        "owner": "Owner",
        "due": "Due",
        "not_stated": "not stated",
        "draft": "AI draft. Check names, decisions and action owners "
                 "against the recording before sharing.",
    },
    "sw": {
        "summary": "Muhtasari",
        "decisions": "Maamuzi",
        "actions": "Hatua za kuchukua",
        "discussion": "Majadiliano kwa mada",
        "open": "Masuala yaliyobaki wazi",
        "task": "Kazi",
        "owner": "Mhusika",
        "due": "Tarehe",
        "not_stated": "haikutajwa",
        "draft": "Rasimu ya AI. Hakiki majina, maamuzi na wahusika wa kazi "
                 "kwa kulinganisha na rekodi kabla ya kuisambaza.",
    },
}


# ---------------------------------------------------------------- transcript

def _clock(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def load_transcript(path: Path) -> str:
    """Plain text as is; JSON as a 'text' field or a list of segments."""
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() != ".json":
        return raw.strip()
    data = json.loads(raw)
    segments = data.get("segments") if isinstance(data, dict) else data
    if isinstance(segments, list) and segments and all(
            isinstance(s, dict) and "text" in s for s in segments):
        lines = []
        for s in segments:
            stamp = (f"[{_clock(s['start'])}] "
                     if isinstance(s.get("start"), (int, float)) else "")
            speaker = f"{s['speaker']}: " if s.get("speaker") else ""
            lines.append(f"{stamp}{speaker}{str(s['text']).strip()}")
        return "\n".join(lines)
    if isinstance(data, dict) and isinstance(data.get("text"), str):
        return data["text"].strip()
    raise SystemExit(f"{path.name}: expected a 'text' field or a list of "
                     "segments that each have 'text'.")


def split_chunks(text: str, max_words: int) -> list[str]:
    """Pack lines (or sentences, when there are no line breaks) into chunks
    of at most max_words words, never splitting inside a line or sentence
    unless that one line is itself longer than a chunk."""
    units = [u.strip() for u in re.split(r"\n+|(?<=[.!?])\s+", text)
             if u.strip()]
    chunks: list[str] = []
    current: list[str] = []
    count = 0

    def flush() -> None:
        nonlocal current, count
        if current:
            chunks.append("\n".join(current))
            current, count = [], 0

    for unit in units:
        words = unit.split()
        while len(words) > max_words:
            flush()
            chunks.append(" ".join(words[:max_words]))
            words = words[max_words:]
        if not words:
            continue
        if count + len(words) > max_words:
            flush()
        current.append(" ".join(words))
        count += len(words)
    flush()
    return chunks


def _words(text: str) -> int:
    return len(text.split())


# ------------------------------------------------------------------- model

class ModelError(SystemExit):
    """A setup problem the user can fix; printed without a traceback."""


@dataclass
class LocalModel:
    url: str = DEFAULT_URL
    model: str = DEFAULT_MODEL
    api: str = "ollama"          # "ollama" or "openai"
    num_ctx: int = 8192
    timeout: float = 900.0

    def chat(self, system: str, user: str, max_tokens: int) -> str:
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": user}]
        base = self.url.rstrip("/")
        if self.api == "ollama":
            # Ollama's native endpoint, because it is the only one that takes
            # num_ctx. Without it Ollama silently cuts long prompts to its
            # small default window and the report misses most of the section.
            data = self._post(base + "/api/chat", {
                "model": self.model, "messages": messages, "stream": False,
                "options": {"num_ctx": self.num_ctx, "num_predict": max_tokens,
                            "temperature": 0.3, "top_p": 0.8, "top_k": 20},
            })
            text = (data.get("message") or {}).get("content", "")
            cut = data.get("done_reason") == "length"
            # Ollama drops the start of a prompt that does not fit, with no
            # error. Kiswahili takes more tokens per word than English, so
            # say so when a section came close to the window.
            if data.get("prompt_eval_count", 0) + max_tokens > self.num_ctx:
                print(f"  warning: this section nearly filled the "
                      f"{self.num_ctx}-token window and may have been cut; "
                      "rerun with a lower --chunk-words or a higher "
                      "--num-ctx", file=sys.stderr)
        else:
            data = self._post(base + "/v1/chat/completions", {
                "model": self.model, "messages": messages,
                "max_tokens": max_tokens, "temperature": 0.3, "top_p": 0.8,
            })
            choice = data["choices"][0]
            text = choice["message"]["content"] or ""
            cut = choice.get("finish_reason") == "length"
        if cut:
            print("  warning: the model hit its output limit; this part may "
                  "be cut short", file=sys.stderr)
        return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()

    def _post(self, endpoint: str, body: dict) -> dict:
        req = urllib.request.Request(
            endpoint, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 404 and "not found" in detail.lower():
                hint = (f"Download it first:\n    ollama pull {self.model}"
                        if self.api == "ollama" else
                        "Load that model in your local server first.")
                raise ModelError(f"Model '{self.model}' is not on this "
                                 f"computer yet. {hint}") from None
            raise ModelError(f"The local model server answered {e.code}: "
                             f"{detail}") from None
        except (socket.timeout, TimeoutError):
            raise ModelError(
                f"No answer within {self.timeout:.0f}s. Raise --timeout, or "
                "lower --chunk-words so each section is smaller.") from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise ModelError(
                    f"No answer within {self.timeout:.0f}s. Raise --timeout, "
                    "or lower --chunk-words.") from None
            start = ("Open the Ollama app (or run `ollama serve`)"
                     if self.api == "ollama" else "Start your local server")
            raise ModelError(f"Cannot reach a local model at {self.url} "
                             f"({e.reason}). {start} and try again.") from None


# ----------------------------------------------------------------- prompts

PARTS = ("TOPICS: what was discussed, with key points and figures\n"
         "DECISIONS: what was agreed or decided\n"
         "ACTIONS: task - owner - deadline (write \"{ns}\" when the owner or "
         "deadline is not said)\n"
         "QUESTIONS: issues raised but left unresolved")


def section_prompt(title, i, n, chunk, in_lang, out_lang, h):
    system = ("You take notes on one section of a meeting transcript. Write "
              "only what the transcript says. Never invent names, numbers, "
              f"dates or decisions. Write in {out_lang}.")
    user = (f"Meeting: {title}\n"
            f"Section {i} of {n}. The transcript is in {in_lang}; write the "
            f"notes in {out_lang}.\n\n"
            "Return these four parts, each a short bullet list. Write "
            "\"none\" for an empty part.\n"
            f"{PARTS.format(ns=h['not_stated'])}\n\n"
            f"Transcript section:\n\"\"\"\n{chunk}\n\"\"\"")
    return system, user


def merge_prompt(title, notes, out_lang, h):
    system = ("You merge meeting notes. Keep every decision, action, owner, "
              "number and date exactly as written; drop only repetition. "
              f"Write in {out_lang}.")
    user = (f"Meeting: {title}\n"
            "Merge these notes from consecutive parts of the meeting into one "
            "set of notes with the same four parts:\n"
            f"{PARTS.format(ns=h['not_stated'])}\n\n" + "\n\n".join(notes))
    return system, user


def report_prompt(title, notes, out_lang, h):
    system = ("You write meeting reports from section notes. Use only facts "
              "in the notes. Merge duplicates. Keep names, numbers and dates "
              f"exactly as written. Write in {out_lang}.")
    user = (f"Meeting: {title}\n"
            f"Below are notes from {len(notes)} consecutive parts of the "
            "meeting, in order.\n\n"
            "Write the report in Markdown with exactly these headings, in "
            "this order, and nothing before the first heading:\n"
            f"## {h['summary']}\n(one paragraph, 4-6 sentences)\n"
            f"## {h['decisions']}\n(bullet list)\n"
            f"## {h['actions']}\n(a table with columns {h['task']} | "
            f"{h['owner']} | {h['due']}; write \"{h['not_stated']}\" where "
            "the notes do not say)\n"
            f"## {h['discussion']}\n(one ### subheading per main topic, "
            "with short bullets)\n"
            f"## {h['open']}\n(bullet list)\n\n"
            "Notes:\n\n" + "\n\n".join(
                f"### Part {i}\n{n}" for i, n in enumerate(notes, 1)))
    return system, user


# ---------------------------------------------------------------- pipeline

def _load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_report(model: LocalModel, transcript: str, title: str,
                 in_lang: str, out_lang: str, chunk_words: int,
                 cache_path: Path | None = None, log=print) -> str:
    h = HEADINGS[out_lang]
    in_name, out_name = LANG_NAMES[in_lang], LANG_NAMES[out_lang]
    chunks = split_chunks(transcript, chunk_words)
    if not chunks:
        raise SystemExit("The transcript is empty.")

    cache = _load_cache(cache_path) if cache_path else {}
    notes: list[str] = []
    log(f"{_words(transcript)} words in {len(chunks)} section(s); "
        f"model {model.model}")
    for i, chunk in enumerate(chunks, 1):
        key = hashlib.sha256(
            f"{model.model}|{out_lang}|{title}|{chunk}".encode()).hexdigest()
        if key in cache:
            log(f"  section {i}/{len(chunks)}: reused from the last run")
            notes.append(cache[key])
            continue
        started = time.monotonic()
        system, user = section_prompt(title, i, len(chunks), chunk,
                                      in_name, out_name, h)
        note = model.chat(system, user, max_tokens=1200)
        notes.append(note)
        if cache_path:
            cache[key] = note
            cache_path.write_text(json.dumps(cache, ensure_ascii=False,
                                             indent=1), encoding="utf-8")
        log(f"  section {i}/{len(chunks)}: "
            f"{time.monotonic() - started:.0f}s")

    # The final prompt must fit the context window too. Merge neighbouring
    # notes in pairs or more until it does; each round shrinks the list.
    budget = chunk_words
    while len(notes) > 1 and sum(map(_words, notes)) > budget:
        groups, group, size = [], [], 0
        for note in notes:
            if len(group) >= 2 and size + _words(note) > budget:
                groups.append(group)
                group, size = [], 0
            group.append(note)
            size += _words(note)
        groups.append(group)
        log(f"  combining {len(notes)} sets of notes into {len(groups)}")
        notes = [g[0] if len(g) == 1 else
                 model.chat(*merge_prompt(title, g, out_name, h),
                            max_tokens=1500) for g in groups]

    log("  writing the report")
    body = model.chat(*report_prompt(title, notes, out_name, h),
                      max_tokens=3000)
    langs = (f"Spoken in {in_name}, report in {out_name}" if out_lang == "en"
             else f"Lugha ya mkutano: {in_name}; ripoti: {out_name}")
    return (f"# {title}\n\n_{h['draft']}_\n\n"
            f"_{langs}. Written on this computer by {model.model}, "
            f"{date.today().isoformat()}._\n\n{body.strip()}\n")


# --------------------------------------------------------------------- cli

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Write a meeting report with a local model "
                    "(no API key, no credits).")
    p.add_argument("transcript", nargs="?", type=Path,
                   help=".txt or .json transcript saved by the assistant")
    p.add_argument("--title", help="meeting title (default: file name)")
    p.add_argument("--language", choices=LANG_NAMES, default="en",
                   help="language spoken in the meeting")
    p.add_argument("--report-language", choices=["same", *LANG_NAMES],
                   default="same")
    p.add_argument("--out", type=Path,
                   help="report file (default: <transcript>.report.md)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--url", default=DEFAULT_URL,
                   help="local server (Ollama: http://localhost:11434, "
                        "llama-server: http://localhost:8080)")
    p.add_argument("--api", choices=["ollama", "openai"], default="ollama",
                   help="'openai' for llama-server, LM Studio and other "
                        "OpenAI-compatible local servers")
    p.add_argument("--num-ctx", type=int, default=8192,
                   help="context window to ask Ollama for (tokens)")
    p.add_argument("--chunk-words", type=int, default=1800,
                   help="transcript words per section; lower it if a "
                        "section is slow or runs out of memory")
    p.add_argument("--timeout", type=float, default=900,
                   help="seconds to wait for one answer")
    p.add_argument("--check", action="store_true",
                   help="only check that the local model answers")
    args = p.parse_args(argv)
    if not args.check and not args.transcript:
        p.error("give a transcript file, or --check")
    return args


def main(argv=None) -> int:
    # A Windows console or redirected output may not be UTF-8; never crash
    # on a model's curly quote or dash.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    args = parse_args(argv)
    model = LocalModel(url=args.url, model=args.model, api=args.api,
                       num_ctx=args.num_ctx, timeout=args.timeout)
    if args.check:
        started = time.monotonic()
        reply = model.chat("Answer in one short sentence.",
                           "Say hello in English and in Kiswahili.", 60)
        print(f"OK in {time.monotonic() - started:.0f}s - {model.model}: "
              f"{reply}")
        return 0

    out_lang = (args.language if args.report_language == "same"
                else args.report_language)
    out = args.out or args.transcript.with_suffix(".report.md")
    report = write_report(
        model, load_transcript(args.transcript),
        args.title or args.transcript.stem, args.language, out_lang,
        args.chunk_words,
        cache_path=out.with_name(out.name + ".notes.json"))
    out.write_text(report, encoding="utf-8")
    print(f"Report saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
