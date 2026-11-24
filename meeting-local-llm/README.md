# Local meeting reports (no credits)

Writes the meeting report from a saved transcript with a model that runs on
your own computer. It doesn't use OpenRouter, an API key or credits.

It fixes the "OpenRouter needs more credit" error. That error comes from the
report step, so the meeting doesn't need to be transcribed again: the
transcript is already saved.

## Models (checked on Hugging Face, 24 Nov 2026)

| Step | Model | Size | Notes |
|---|---|---|---|
| Report (default) | [unsloth/Qwen3-4B-Instruct-2507-GGUF](https://hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF) `Q4_K_M` | 2.5 GB | Apache-2.0; 4B instruct model, no thinking blocks |
| Report, Kiswahili alternative | [google/gemma-4-E4B-it-qat-q4_0-gguf](https://hf.co/google/gemma-4-E4B-it-qat-q4_0-gguf) | 5.2 GB | Apache-2.0; Google's official Q4 build; 140+ languages |
| Transcription | [Systran/faster-whisper-small](https://hf.co/Systran/faster-whisper-small) | 0.5 GB | MIT; multilingual incl. Swahili; runs on CPU |
| Transcription, more accurate | [deepdml/faster-whisper-large-v3-turbo-ct2](https://hf.co/deepdml/faster-whisper-large-v3-turbo-ct2) | 1.6 GB | MIT; slower on CPU |

No training is needed to start. Fine-tune only after you have measured where
these models go wrong on your own recordings.

## Setup on Windows (once)

1. Install Ollama from https://ollama.com/download and open it.
2. Download the report model (2.5 GB):

```powershell
ollama pull hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M
```

3. Check that it answers:

```powershell
python local_report.py --check
```

## Write the report for a saved meeting

Point it at the transcript file the assistant saved for that meeting (`.txt`,
or `.json` with a `text` field or a list of segments):

```powershell
python local_report.py "path\to\transcript.txt" --title "Day 5 RCC Morning session"
```

The report is saved next to the transcript as `transcript.report.md`.

Options:

- `--language sw` if the meeting was in Kiswahili
- `--report-language en` to write a Kiswahili meeting's report in English
- `--model ...` to use another model you've pulled into Ollama
- `--api openai --url http://localhost:8080 --model local` for llama.cpp's
  `llama-server` or LM Studio instead of Ollama
- `--chunk-words 1200` if a section is too slow or runs out of memory

## How it works

An 87-minute meeting is about 11,000 spoken words, which is too much for a
small model to read in one go on a laptop. The script:

1. splits the transcript into sections of 1,800 words,
2. takes notes on each section (topics, decisions, actions with owner and
   deadline, open questions),
3. merges the notes if they're still too long,
4. writes the report with fixed headings in English or Kiswahili.

Each finished section is saved to `transcript.report.md.notes.json`. If the
run stops, running the same command again starts from the last finished
section.

It always asks Ollama for an 8,192-token context window (`--num-ctx`).
Without that setting, Ollama cuts long prompts to its smaller default and the
report misses parts of the meeting without any error.

The report is an AI draft. Check names, decisions and action owners against
the recording before sharing it.

## Tests

```powershell
python -m unittest test_local_report -v
```

The tests run the whole flow against a fake local server, so they need no
model download. They don't measure report quality or speed on your laptop.
