# Web application

Shows the four-language reasoning model doing the thing the project is about:
**reasoning and language fidelity as separate, visible facts**.

Three views:

- **Try it** — ask in any of the four languages. The think block and the final
  answer are displayed as separate panels, each with its own detected-language
  badge, plus a language-mixture bar for the reasoning. When a Wolof question
  comes back with English reasoning, the page says so in as many words. A UI
  that concatenated thinking and answer would hide exactly the failure this
  project exists to catch.
- **Before / after** — the held-out comparison from `results/comparison.json`,
  per language, with deltas. Less collapse is an improvement, so that row is
  coloured in the opposite direction to the others.
- **Data status** — per-language verification state. While nothing is natively
  verified, the page says so prominently. A demo that hides its own data
  provenance is how unverified work gets mistaken for finished work.

## Run it

```bash
pip install fastapi uvicorn

# Interface only, no model. Useful for reviewing the UI, and it works on a
# laptop with no GPU.
python webapp/server.py --stub

# With a trained adapter (needs a GPU for a 4.5B base)
python webapp/server.py --manifest artifacts/serve/serve_manifest.json

# CPU serving via a quantized GGUF -- also the phase-two on-device path
python webapp/server.py --gguf artifacts/serve/gguf/gemma4-mlr-Q4_K_M.gguf
```

Then open <http://127.0.0.1:8000>.

## API

| endpoint | returns |
|---|---|
| `GET /api/status` | mode, backend, manifest, active Wolof–French tolerance, warnings |
| `GET /api/results` | before/after comparison (404 until you have run an evaluation) |
| `GET /api/data` | per-language verification state of the training corpus |
| `POST /api/generate` | `{question, language}` → think block, answer, per-part language, collapse flag |

`/api/generate` scores its own output with the same `format_guard` and `langid`
code the offline evaluation uses, so what the page displays and what the
metrics count are the same judgement, not two implementations that can disagree.

## Where the model comes from

`serve_manifest.json`, written by `scripts/export_model.py`, is the contract:
it names the artifact kind, the paths, the thinking delimiters and the data
fingerprint. If it records `trained_on_unverified_data: true`, the app shows a
standing warning and there is no way to switch it off from the interface.
