# Provenance

Document similarity and AI-writing detection, built on free infrastructure.

A credit-based service in the shape of the commercial products: upload a
document, spend a credit, get a report showing which passages appear elsewhere
and where. It is **not** a Turnitin client and does not use their index, their
API or their marks.

Phase 0 and the similarity engine are built and tested. AI-writing detection is
implemented but deliberately inert until a calibration is fitted — see
[Honest limits](#honest-limits) below, which is the part of this README worth
reading before the install instructions.

---

## Run it

No database server, no Redis, no build step.

```bash
cd provenance
pip install -r requirements.txt
python -m apps.api.main          # http://localhost:8000
```

Sign up in the browser; new accounts get three credits. To open a dashboard
that already has completed reports on it:

```bash
python scripts/seed_demo.py
PROVENANCE_DB=data/demo.db PROVENANCE_CORPUS=data/demo-corpus.db \
  python -m apps.api.main
# demo@provenance.local / demo-password
```

Tests:

```bash
python -m pytest tests/ -q       # 71 tests
```

---

## What it actually does

Three engines, and only one of them is a language model. That distinction is
the whole design.

| Job | Problem class | Implementation |
|---|---|---|
| **Similarity** | Information retrieval | Winnowed fingerprints over an inverted index |
| **AI detection** | Calibrated classification | Binoculars, gated on a fitted calibration |
| **Explanation** | Generation | Free-tier LLM router (`providers.py`) |

Asking an LLM "is this plagiarised?" does not work: it has no index to check
against and no way to know it is guessing, so it invents sources. The free LLM
tiers earn their place writing report prose, adjudicating borderline paraphrase
matches, and generating classifier training data. They never decide a verdict.

### Retrieval: winnowing, not MinHash LSH

The first implementation used MinHash with banded LSH and it was wrong — worth
recording, because it is the obvious approach.

MinHash estimates *global* Jaccard overlap. A thesis that copies one chapter out
of twelve has a global Jaccard around 0.05 against its source. Tune LSH to
surface that and it returns half the corpus for every query; tune it to be
useful and it never surfaces it at all. Measured on the test pair in
`test_detector.py`: true Jaccard 0.258, LSH threshold ≈ 0.42, zero shared bands,
**zero matches on a document whose first paragraph was copied verbatim**.

The fix is [winnowing](https://dl.acm.org/doi/10.1145/872757.872770) (Schleimer,
Wilkerson & Aiken, SIGMOD 2003 — the algorithm behind MOSS) over an inverted
index. Hash every word 5-gram, slide a window of 8, keep the minimum in each
window. Any shared passage of ≥ 12 words is guaranteed to produce a shared
fingerprint, at about 22% storage density. Whole-document near-duplicate
detection and passage-level reuse detection are different problems, and only the
second one is plagiarism detection.

MinHash survives, demoted to scoring how similar two documents are overall once
the index has decided they are worth comparing.

### The similarity score

The fraction of *scored* words inside at least one matched span. Overlapping
matches from different sources are unioned before counting, so a passage found
in three places counts once. Quotations and the reference list are excluded from
both the numerator and the denominator, so padding a paper with block quotes
neither helps nor hurts.

---

## Honest limits

**The corpus is the constraint, not the compute.** Turnitin's advantage is an
index of over a billion student papers that you cannot obtain. What this
searches today is documents previously submitted to *this* deployment. That is
genuinely useful — it catches collusion within a cohort, which is the case that
actually happens — and it is not parity. Phase 3 adds CORE (49.2M full texts),
OpenAlex (250M works, CC0) and Wikipedia.

**AI detection is off until you calibrate it.** A Stanford study found detectors
flagged [61.3% of TOEFL essays by non-native English speakers](https://arxiv.org/pdf/2304.02819)
as machine-written: second-language writers use regular syntax and common
vocabulary, which is exactly the signal these methods key on. `BinocularsDetector`
therefore raises `UncalibratedError` rather than emitting a probability, and
`load_detector()` returns `NullAiDetector` when no calibration file exists. A
report then says *AI detection did not run*, which is honest, rather than 0%,
which would not be. See [docs/AI_DETECTION.md](docs/AI_DETECTION.md).

**Demo mode fabricates everything.** `PROVENANCE_DEMO_MODE=1` swaps in
`MockDetector`, which invents plausible results so the product can be
demonstrated with no models installed. Every such report carries `is_mock`, the
UI shows a banner, and `detector_versions.warning` reads `FABRICATED RESULTS`.
Never set it on a deployment anyone relies on.

**Storing student work needs consent.** Sign-up carries a real checkbox. A user
who declines still gets their reports; their document simply never joins the
corpus others are searched against, enforced in the pipeline rather than the UI.

---

## Layout

```
packages/detector/     Pure Python. Standard library only in its default config.
  extract.py           .txt/.md/.docx with the stdlib; .pdf needs pymupdf
  segment.py           sentences, paragraphs, shingles, quote/reference masking
  fingerprint.py       winnowing, inverted index, MinHash, span alignment
  corpus.py            SQLite-backed document store
  aidetect.py          Binoculars + the Calibration gate
  providers.py         free-tier LLM router with failover, cache and budget
  pipeline.py          the nine stages
  mock.py              MockDetector

apps/api/              FastAPI: auth, credits, submissions, reports
  credits.py           append-only ledger, idempotent, BEGIN IMMEDIATE
  jobs.py              in-process queue and worker thread
  static/              the dashboard (vanilla JS, no build step)

tests/                 71 tests, including the phase gates
scripts/seed_demo.py   demo account, codes and a small corpus
```

`packages/detector` imports nothing from the web app. CI proves the
standard-library claim by running the pipeline with no third-party packages
installed.

### Why SQLite and vanilla JS

Both are deliberate, and both are swaps rather than rewrites when outgrown.
SQLite means no `docker compose up` before a contributor's first test run, and
the schema is ordinary SQL that Postgres accepts. No build step means deployment
is `pip install && python -m apps.api.main`, which every remaining free tier will
run. The reference product uses Laravel + Inertia + React + Tailwind v4 +
shadcn/ui; the design language here matches it, so swapping the front end
changes the implementation and not the look.

---

## Deploying free

**Render free tier** ([`render.yaml`](render.yaml) is committed) is the pick. It
is the last remaining free plan that runs a persistent Python process with a
background worker — Heroku's free tier is gone, Fly removed theirs, and Koyeb
closed its Starter tier to new users after the Mistral acquisition in early 2026.

Two things to know before you rely on it:

- Free web services **spin down after 15 minutes** of inactivity; the next
  request takes 30–50 seconds to wake. Fine for submit-and-wait, awkward for a
  live demo — warm it first.
- Free instances have **no persistent disk**. The SQLite corpus is wiped on
  every deploy. Attach a disk, or point `PROVENANCE_DB` at a free
  [Neon](https://neon.tech) Postgres, before anything needs to survive.

For the Phase 4 AI-detection worker, put Binoculars on a **Hugging Face Space**
(Docker SDK, free CPU) rather than the web dyno — model loading will not fit in
a free web instance's memory or startup budget.

---

## Configuration

Every value has a working default; nothing needs setting to run locally. See
[`.env.example`](.env.example).

| Variable | Default | Notes |
|---|---|---|
| `PROVENANCE_DB` | `./data/provenance.db` | Users, credits, submissions |
| `PROVENANCE_CORPUS` | `./data/corpus.db` | The searchable corpus |
| `PROVENANCE_CALIBRATION` | unset | Absent ⇒ AI detection does not run |
| `PROVENANCE_DEMO_MODE` | `0` | `1` fabricates every report |
| `PROVENANCE_SECURE_COOKIES` | `0` | Set to `1` behind HTTPS |
| `PROVENANCE_MAX_UPLOAD_MB` | `20` | |

Free-tier LLM keys (`CEREBRAS_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`,
`OPENROUTER_API_KEY`) are optional and used only for generation work.

---

## Roadmap

| Phase | Status | Gate |
|---|---|---|
| 0 · Skeleton and mock | **done** | Upload → every stage → report, no model installed |
| 1 · Accounts, credits, queue | **done** | Ledger balance survives 100 randomised cycles |
| 2 · Extraction + internal similarity | **done** | Edited copy scores > 80% with correct spans |
| 3 · External corpus + paraphrase | next | Beats verbatim-only recall without raising FPR |
| 4 · AI detection v1 | not started | Acceptable recall at 1% FPR on the control set |
| 5 · Kaggle fine-tune | conditional | Only if Phase 4's gate fails |
| 6 · Report viewer + deploy | partial | 20 pages end-to-end in under five minutes |

Phase gates are executable: `test_phase0_gate_full_round_trip`,
`test_phase1_gate_randomised_cycles`, `test_phase2_gate_lightly_edited_copy`.

## Licence

Not yet chosen. Pick one before publishing.
