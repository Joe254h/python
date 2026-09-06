# Data plan, and a correction to the starting assumption

## What the upstream dataset actually contains

`HuggingFaceH4/Multilingual-Thinking` is about **1,000 rows**, sampled from the
SystemChat subset of SmolTalk2, whose English chain-of-thought was translated
by a language model into **Spanish, French, Italian and German**.

That is the whole language list. There is no Swahili and no Wolof in it, and
English appears as the *source* the traces were translated from rather than as
a labelled target language.

This matters for the instruction "keep English and French, translate into
Wolof and Swahili, drop every other language". Applied literally:

| step | rows |
|---|---|
| upstream total | ~1,000 |
| drop Spanish, Italian, German | ~250 French remain |
| English source traces | recoverable for all ~1,000 |

So the four-language set is roughly **250 French rows plus their English
sources**, not a large multilingual pool that Swahili and Wolof are added to.

This is not a problem — it is close to the target size your own protocol
argues for. 300 clean examples beat 5,000 noisy ones, and 250 French rows with
English sources, translated carefully into Swahili and Wolof and validated, is
a ~250-item four-language set. It does mean the budget is fixed by validation
capacity rather than by the size of the download, which is the right
constraint for low-resource work anyway.

**Decision needed:** cap at ~250 upstream rows, or top up from another source
(GSM8K-style problems, or locally authored items grounded in Senegalese and
Kenyan contexts) to reach 300? My recommendation is to cap at what can be
natively validated and not to top up — the binding constraint is Wolof review
capacity, not row count, and unvalidated rows would dilute exactly the quality
the protocol is protecting.

## Format conversion

The upstream rows are gpt-oss **Harmony** records: reasoning lives in a
separate `thinking` field beside `content`, not in inline delimiters. Gemma 4
instead uses an inline thinking channel. So ingestion is a real conversion
step, not a passthrough, and it is where the format is most likely to break.

`src/mlr/format_guard.py` validates every converted row: exactly one think
block, non-empty on both sides, no delimiter fragments leaked into content,
and digit-for-digit numeric parity with the source.

## The 20 examples in this repository

Because `huggingface.co` is blocked (see `BLOCKERS.md`), the 20 examples in
`data/sample20/` are **authored in the upstream schema and style, not drawn
from the upstream dataset**. Every row carries `upstream_id: null` to keep
that unambiguous.

They are still doing real work: they exercise the translation, validation and
format tooling end to end, and they give the Wolof reviewer a concrete set to
calibrate on. When HF is reachable, real rows replace them and the Swahili and
Wolof work here stays useful as a translation reference and a style guide.
