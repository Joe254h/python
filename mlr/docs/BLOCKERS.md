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

- **The Gemma 4 thinking delimiters.** RESOLVED IN CODE -- the constants are no
  longer trusted. `detect_thinking_format()` in `src/mlr/format_guard.py` works
  the delimiters out from the tokenizer's own chat template at load time, and
  overrides whatever is configured. `scripts/inspect_chat_template.py` prints
  what it found, tokenizer only, in a few seconds.

  A first Kaggle run confirmed the guess was wrong, and also exposed a worse
  bug it was hiding: the old check demanded that `<|channel>thought\n` be a
  single vocabulary entry, which no composite delimiter ever is, so it would
  have failed even with the right spelling. See "the prompt-opened block"
  below.
- **The upstream dataset's language list.** See `docs/DATA_PLAN.md` -- this one
  changes the project's data budget and needs a decision.

## 4. Resolved: the chat template may open the reasoning block

The first real run against Gemma 4 surfaced something no amount of offline
reasoning would have settled: whether the chat template emits the *opening*
thinking marker as part of the generation prompt.

It matters more than the spelling of the delimiters. If the template opens the
block, then:

- the model's output starts *inside* the reasoning block and contains no
  opening marker, so a parser that demands one scores every correct generation
  as a format failure -- which looks like catastrophic model breakage and is
  not;
- a training target that includes the marker teaches the model to emit a
  second one on top of the template's.

`ThinkingFormat.open_emitted_by_template` now carries this, detection sets it,
`parse()` respects it, and `training_target()` omits the marker when the
template supplies it. Twelve tests in `tests/test_format_detection.py` pin the
behaviour down against mock tokenizers shaped like the conventions real
thinking models use.

## 5. Watch for: transformers too old for Gemma 4

A first Kaggle run printed:

    You are using a model of type gemma4 to instantiate a model of type .

That warning means the installed `transformers` does not fully recognise the
`gemma4` architecture. The tokenizer still loads, so it is not immediately
fatal, but the model class may fall back to something generic. If model loading
fails or behaves oddly, upgrade first:

    pip install -U "transformers>=4.57"

and re-run `scripts/inspect_chat_template.py` to confirm the template renders.
