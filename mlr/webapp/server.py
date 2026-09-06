#!/usr/bin/env python3
"""Web application for the four-language reasoning model.

Serves three things:

  * live inference, showing the THINK BLOCK and the FINAL ANSWER separately,
    each with its detected language -- because that separation is the whole
    thesis of the project, and a UI that concatenates them hides the failure
    it exists to expose;
  * the before/after comparison from results/comparison.json;
  * the data verification status, so a model trained on unverified Wolof
    cannot be demoed as though it were finished.

Run it:
    python webapp/server.py --stub                              # no model, UI only
    python webapp/server.py --manifest artifacts/serve/serve_manifest.json
    python webapp/server.py --gguf artifacts/serve/gguf/model-Q4_K_M.gguf
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, HTTPException                       # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse         # noqa: E402
from pydantic import BaseModel, Field                            # noqa: E402

from mlr.format_guard import GEMMA4_THINKING as FMT, parse       # noqa: E402
from mlr.langid import identify, code_switch_ratio               # noqa: E402
from mlr.evaluation import language_ok, WOLOF_FRENCH_TOLERANCE   # noqa: E402
from mlr.backends import baseline_system_prompt, LANG_NAME       # noqa: E402

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="Gemma 4 four-language reasoning")
STATE: dict = {"backend": None, "manifest": None, "mode": "stub"}


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="sw", pattern="^(en|fr|sw|wo)$")
    max_new_tokens: int = Field(default=512, ge=32, le=2048)


class StubBackend:
    """Scripted responses so the interface can be used and reviewed with no model.

    Deliberately returns an English reasoning block for Wolof, so the collapse
    detection is visible in the UI rather than only in a test file.
    """

    name = "stub (no model loaded)"

    THINK = {
        "en": "First I read the question and identify what is being asked. Then I work through the steps in order and check the result.",
        "fr": "D'abord je lis la question et j'identifie ce qui est demandé. Ensuite je travaille les étapes dans l'ordre et je vérifie le résultat.",
        "sw": "Kwanza ninasoma swali na kutambua kinachoulizwa. Kisha ninafanya hatua kwa mpangilio na kuangalia jibu.",
        "wo": "Bu njëkk damay jàng laaj bi te xam lu ñu laaj. Ba noppi ma jëfandikoo yëf yi ci tolluwaay bi te seet njariñ li.",
    }
    ANSWER = {
        "en": "This is a stub answer. No model is loaded.",
        "fr": "Ceci est une réponse fictive. Aucun modèle n'est chargé.",
        "sw": "Hili ni jibu la mfano. Hakuna modeli iliyopakiwa.",
        "wo": "Lii tontu bu njumtukaay la. Amul benn modil bu ñu duggal.",
    }

    def generate(self, system: str, user: str, max_new_tokens: int = 512) -> str:
        lang = next((L for L in ("wo", "sw", "fr", "en")
                     if LANG_NAME[L] in system), "en")
        # Wolof deliberately collapses to English reasoning, to demonstrate the
        # detector in the UI.
        think = self.THINK["en" if lang == "wo" else lang]
        return FMT.wrap(think, self.ANSWER[lang])


def load_backend(args) -> object:
    if args.stub:
        return StubBackend()
    if args.gguf:
        from mlr.backends import LlamaCppBackend
        print(f"loading GGUF {args.gguf} ...")
        return LlamaCppBackend(model_path=args.gguf, n_threads=args.threads)

    manifest = STATE["manifest"] or {}
    base = args.base or manifest.get("base_model")
    if not base:
        raise SystemExit("no base model: pass --base, --manifest or --stub")

    from mlr.backends import TransformersBackend
    print(f"loading base {base} ...")
    backend = TransformersBackend(model_id=base)
    adapter = args.adapter or manifest.get("adapter_path")
    if adapter and Path(adapter).exists():
        from peft import PeftModel
        print(f"applying adapter {adapter} ...")
        backend.model = PeftModel.from_pretrained(backend.model, adapter)
        backend.model.eval()
        backend.name = f"{base} + {Path(adapter).name}"
    return backend


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/api/status")
def status() -> dict:
    manifest = STATE["manifest"] or {}
    unverified = manifest.get("trained_on_unverified_data", True)
    warnings = []
    if STATE["mode"] == "stub":
        warnings.append("No model is loaded. Responses are scripted placeholders.")
    if unverified:
        warnings.append(
            "This model was trained on data no native speaker has verified. "
            "Wolof in particular is unreviewed machine translation. Treat any "
            "output as a pipeline demonstration, not a result.")
    return {
        "mode": STATE["mode"],
        "backend": getattr(STATE["backend"], "name", "none"),
        "languages": [{"code": c, "name": n} for c, n in LANG_NAME.items()],
        "manifest": manifest or None,
        "wolof_french_tolerance": WOLOF_FRENCH_TOLERANCE,
        "warnings": warnings,
    }


@app.get("/api/results")
def results() -> dict:
    data = read_json(ROOT / "results/comparison.json")
    if data is None:
        raise HTTPException(404, "No comparison yet. Run scripts/run_eval.py --mode compare.")
    return data


@app.get("/api/data")
def data_status() -> dict:
    """Verification status of the training corpus, per language."""
    path = ROOT / "data/sample20/sample20.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_lang: dict[str, dict] = {}
    for r in rows:
        e = by_lang.setdefault(r["lang"], {"rows": 0, "human_verified": 0,
                                           "status": r["verification"], "open_points": 0})
        e["rows"] += 1
        e["human_verified"] += bool(r.get("human_verified"))
        e["open_points"] += len(r.get("review_notes") or [])
    return {
        "total_rows": len(rows),
        "by_language": by_lang,
        "any_human_verified": any(v["human_verified"] for v in by_lang.values()),
    }


@app.post("/api/generate")
def generate(req: Ask) -> JSONResponse:
    backend = STATE["backend"]
    if backend is None:
        raise HTTPException(503, "no backend loaded")

    system = baseline_system_prompt(req.language)
    t0 = time.time()
    try:
        raw = backend.generate(system, req.question, req.max_new_tokens)
    except Exception as exc:                                    # noqa: BLE001
        raise HTTPException(500, f"generation failed: {type(exc).__name__}: {exc}")
    elapsed = round(time.time() - t0, 2)

    parsed = parse(raw, FMT)
    if not parsed.ok:
        return JSONResponse({
            "format_ok": False, "problems": parsed.errors, "raw": raw[:4000],
            "seconds": elapsed, "requested_language": req.language,
        })

    r_ok, r_lang, _ = language_ok(parsed.thinking, req.language)
    a_ok, a_lang, _ = language_ok(parsed.answer, req.language)
    think_mix = identify(parsed.thinking).mixture

    return JSONResponse({
        "format_ok": True,
        "problems": [],
        "requested_language": req.language,
        "thinking": parsed.thinking,
        "answer": parsed.answer,
        "thinking_language": r_lang,
        "answer_language": a_lang,
        "thinking_language_ok": r_ok,
        "answer_language_ok": a_ok,
        "collapsed_to_english": req.language != "en" and "en" in (r_lang, a_lang),
        "french_share_of_thinking": round(
            code_switch_ratio(parsed.thinking, "wo", "fr"), 3
        ) if req.language == "wo" else None,
        "thinking_mixture": {k: round(v, 3) for k, v in (think_mix or {}).items()},
        "seconds": elapsed,
    })


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Serve the four-language reasoning model.")
    p.add_argument("--manifest", default="artifacts/serve/serve_manifest.json")
    p.add_argument("--base", default="")
    p.add_argument("--adapter", default="")
    p.add_argument("--gguf", default="")
    p.add_argument("--stub", action="store_true",
                   help="run the interface with no model (scripted responses)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--threads", type=int, default=4)
    args = p.parse_args(argv)

    manifest_path = Path(args.manifest)
    STATE["manifest"] = read_json(manifest_path) if manifest_path.exists() else None
    if STATE["manifest"] is None and not (args.stub or args.base or args.gguf):
        print(f"no manifest at {manifest_path}; starting in --stub mode.\n"
              f"Train and export first, or pass --base/--gguf.", file=sys.stderr)
        args.stub = True

    STATE["backend"] = load_backend(args)
    STATE["mode"] = "stub" if args.stub else "model"
    print(f"backend: {getattr(STATE['backend'], 'name', '?')}")
    print(f"serving on http://{args.host}:{args.port}")

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
