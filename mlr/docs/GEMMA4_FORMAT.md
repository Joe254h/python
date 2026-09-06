# Gemma 4's thinking format — confirmed

Recorded from a real `google/gemma-4-E4B-it` tokenizer dump under
`transformers 5.0.0`. Everything here is observed, not inferred, except where
it says otherwise.

## The delimiters

The chat template concatenates them literally:

```jinja
{{- '<|channel>thought\n' + thinking_text + '\n<channel|>' -}}
```

| | |
|---|---|
| open | `<|channel>thought\n` |
| close | `<channel|>` (the template writes `\n` before it) |
| opened by the template? | **No** |

The leading newline is dropped from the close marker on purpose: the marker
itself is what has to match, and requiring the newline would fail on any
generation that omits it. `parse()` strips the block anyway.

## Thinking is switched on by a token, not by an open channel

This is the part that no amount of offline reasoning would have settled, and
it is why the render-diff heuristic alone was not enough.

```
enable_thinking=True   '<bos><|turn>system\n<|think|>\n<turn|>\n<|turn>user\n…<turn|>\n<|turn>model\n'
enable_thinking=False  '<bos><|turn>user\n…<turn|>\n<|turn>model\n'
```

`enable_thinking=True` injects a **`<|think|>` control token into the first
system turn**. It does *not* pre-open a reasoning channel. Both prompts end at
`<|turn>model\n`, so the model emits both channel markers itself:

* generated text **does** contain `<|channel>thought\n`, and parsing should
  expect it (`open_emitted_by_template=False`);
* training targets **must** include it, or the model learns to skip it.

Some templates do the opposite, which is why `ThinkingFormat` carries the flag
and `detect_thinking_format` works it out per model rather than assuming.

## Consequence for GGUF serving

`llama.cpp`'s `create_chat_completion` has no way to pass `enable_thinking`,
so it would never emit `<|think|>` and would silently give you a
**non-thinking** model. `LlamaCppBackend` therefore renders the prompt itself
and calls `create_completion`:

```
<bos><|turn>system\n<|think|>\n{system}<turn|>\n<|turn>user\n{user}<turn|>\n<|turn>model\n
```

The probe that produced the reference render had empty system content, so the
placement of a non-empty system message is the one **inferred** detail here.
Protocol item 6 requires confirming the thinking mode survives quantization —
run the held-out evaluation against the GGUF and read `format_ok`. If the
think block stops parsing, this template is the first place to look.

## Other special tokens

```
<|turn>  <turn|>            turn delimiters
<|think|>                   enables thinking, injected into the system turn
<|channel>  <channel|>      reasoning channel open/close
<|tool_call>  <tool_call|>  <|tool_response>  <tool_response|>
<|image|> <|audio|> <|video|>          multimodal
<bos> <eos> <pad> <unk> <mask>
```

## Keeping this honest

`resolve_from_tokenizer()` re-derives all of the above at load time, so a
different checkpoint or a template revision corrects the constants rather than
silently disagreeing with them. `tests/test_format_detection.py` pins the
behaviour to the dump above; `scripts/inspect_chat_template.py` reproduces it
for any model in a few seconds, tokenizer only.
