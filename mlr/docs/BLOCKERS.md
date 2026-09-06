# Blockers

Recorded precisely so the next session does not rediscover them.

## 1. Gemma 4 could not be run. Every model host is blocked by egress policy.

The session's network policy denies `CONNECT` to every host that could supply
weights or the upstream dataset:

| host | purpose | result |
|---|---|---|
| `huggingface.co` | Gemma 4 weights, Multilingual-Thinking dataset | **403 at the proxy** |
| `cdn-lfs.huggingface.co`, `hf.co` | HF model/data downloads | blocked |
| `ollama.com`, `registry.ollama.ai` | GGUF quants | blocked |
| `download.pytorch.org` | torch wheels | blocked |
| `kaggle.com` | Gemma mirror | blocked |
| `ai.google.dev`, `arxiv.org` | Gemma 4 documentation | blocked |
| `pypi.org`, `files.pythonhosted.org` | Python packages | reachable |
| `github.com`, `api.github.com` | source | reachable |

This is an organization policy decision, not a transient failure. The proxy
README is explicit that policy denials must be reported rather than retried or
worked around, so no attempt was made to route around it.

**Consequence: there is no baseline in this repository, and there must not be
a number presented as one.** The harness that produces it is written, tested
and ready; it has never seen Gemma 4.

**To unblock:** allow `huggingface.co` and `cdn-lfs.huggingface.co` for this
environment, or supply the weights through a reachable path. Gemma 4 is a
gated model, so an HF token that has accepted the Gemma licence is needed too.

## 2. No GPU in this environment.

4 CPU cores, 15 GB RAM, no CUDA device. This does not block the baseline --
Gemma 4 E2B or E4B as a 4-bit GGUF will run on CPU through `llama.cpp`, which
is why `LlamaCppBackend` exists. Expect roughly 3-8 tokens/sec, so a thinking
model on the 48-item held-out set is on the order of one to two hours. That is
acceptable for a baseline.

It *does* block LoRA fine-tuning (protocol item 4), which needs an accelerator.

## 3. Two facts could not be verified at the source.

Both were taken from secondary sources because the primary documentation is
behind the same egress block. Both are load-bearing, and both are isolated in
one place in the code so they are cheap to correct:

- **The Gemma 4 thinking delimiters** (`<|channel>thought\n` ... `<channel|>`),
  in `ThinkingFormat` in `src/mlr/format_guard.py`. Every format guarantee in
  this project depends on these strings being right.
  `ThinkingFormat.resolve_from_tokenizer()` checks them against the real
  tokenizer and raises if they are wrong; `TransformersBackend` calls it at
  load time, so the first real run will fail loudly rather than silently
  producing unparseable output.
- **The upstream dataset's language list.** See `docs/DATA_PLAN.md` -- this one
  changes the project's data budget and needs a decision.
