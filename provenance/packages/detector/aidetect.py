"""AI-writing detection, and the machinery that stops it being misused.

The detector is Binoculars (Hans et al., ICML 2024): score a passage with two
closely related models -- an observer and a performer -- and take the ratio of
the performer's perplexity to the cross-perplexity between the pair. Human text
surprises the performer more than the observer can account for; machine text
does not. It needs no training data and, in the paper, detects over 90% of
ChatGPT output at a 0.01% false positive rate.

The important code in this module is not the detector. It is `Calibration`.

A raw Binoculars score is a ratio around 1.0 with no probabilistic meaning, and
the single most consequential finding in this literature is that detectors flag
roughly 61% of TOEFL essays by non-native English speakers as machine-written
(Liang et al., 2023). Second-language writers use regular syntax and common
vocabulary, which is exactly the signal these methods key on. So this module
refuses to emit a probability at all until a calibration has been fitted on a
held-out set that includes second-language human writing, and every signal it
does emit carries the measured false positive rate of its own threshold.

`NullAiDetector` is the default. A deployment with no fitted calibration
reports "AI detection did not run", which is honest, rather than a number,
which would not be.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .segment import paragraphs
from .types import AiSignal, Document, Span


class UncalibratedError(RuntimeError):
    """Raised when a probability is requested before a calibration exists."""


@dataclass(frozen=True)
class Calibration:
    """Maps a raw detector score onto a probability, with a measured FPR.

    Fitted by `scripts/fit_calibration.py` against `data/eval/`. The fields are
    a two-parameter logistic (Platt scaling) plus the operating point that was
    chosen, and the FPR that operating point achieved on the second-language
    human control set -- not on the overall negative set, which would be a
    kinder and much less useful number.
    """

    detector: str
    slope: float
    intercept: float
    threshold: float
    fpr_at_threshold: float
    control_set: str
    n_control: int
    #: Half-width of the reported interval, from the bootstrap in the fitting
    #: script. Reported rather than assumed.
    interval_halfwidth: float = 0.1

    def probability(self, raw: float) -> float:
        return 1.0 / (1.0 + math.exp(-(self.slope * raw + self.intercept)))

    def interval(self, p: float) -> tuple[float, float]:
        return (
            max(0.0, p - self.interval_halfwidth),
            min(1.0, p + self.interval_halfwidth),
        )

    @classmethod
    def load(cls, path: str | Path) -> "Calibration":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")


class AiDetector(Protocol):
    name: str

    def score(self, doc: Document) -> list[AiSignal]:
        ...


class NullAiDetector:
    """Runs nothing and says so.

    The default until a calibration exists. Returning an empty list is
    meaningful: `Report.ai_probability` is then None, and the UI is required to
    render "not run" rather than 0%.
    """

    name = "none"

    def score(self, doc: Document) -> list[AiSignal]:
        return []


class BinocularsDetector:
    """Binoculars scoring over paragraphs.

    Model pair defaults to Qwen2.5-0.5B base and instruct, which runs on CPU.
    The paper uses Falcon-7B; that is stronger and needs a GPU, so it is the
    right choice for a worker on Kaggle or a Space and the wrong one for a free
    web dyno. Both are valid -- the pair is a constructor argument and the
    calibration is fitted per pair, which is why `Calibration.detector` records
    which one produced it.
    """

    def __init__(
        self,
        observer: str = "Qwen/Qwen2.5-0.5B",
        performer: str = "Qwen/Qwen2.5-0.5B-Instruct",
        calibration: Calibration | None = None,
        device: str = "cpu",
        max_tokens: int = 512,
    ) -> None:
        self.observer_id = observer
        self.performer_id = performer
        self.calibration = calibration
        self.device = device
        self.max_tokens = max_tokens
        self.name = f"binoculars/{observer.split('/')[-1]}"
        self._loaded = False
        self._tok = None
        self._observer = None
        self._performer = None

    def _load(self) -> None:
        if self._loaded:
            return
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Binoculars needs torch and transformers:\n"
                "  pip install 'torch>=2.5' 'transformers>=4.57'"
            ) from exc

        self._tok = AutoTokenizer.from_pretrained(self.observer_id)
        if self._tok.pad_token is None:
            self._tok.pad_token = self._tok.eos_token
        self._observer = AutoModelForCausalLM.from_pretrained(self.observer_id).to(
            self.device
        ).eval()
        self._performer = AutoModelForCausalLM.from_pretrained(self.performer_id).to(
            self.device
        ).eval()
        self._loaded = True

    def raw_score(self, text: str) -> float:
        """The Binoculars ratio: performer perplexity over cross-perplexity.

        Lower means more machine-like. Returns the ratio unmodified -- turning
        it into a probability is `Calibration`'s job and happens nowhere else.
        """
        import torch

        self._load()
        enc = self._tok(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_tokens,
        ).to(self.device)
        ids = enc.input_ids

        with torch.no_grad():
            obs_logits = self._observer(**enc).logits
            perf_logits = self._performer(**enc).logits

        shift_labels = ids[..., 1:].contiguous()
        obs = obs_logits[..., :-1, :].contiguous()
        perf = perf_logits[..., :-1, :].contiguous()

        # Perplexity of the observed tokens under the performer.
        ce = torch.nn.functional.cross_entropy(
            perf.view(-1, perf.size(-1)), shift_labels.view(-1), reduction="mean"
        )
        ppl = ce.item()

        # Cross-perplexity: the performer's surprise at the observer's own
        # distribution. This is the denominator that normalises away "this text
        # is simply predictable" -- the term that, left out, is what makes
        # naive perplexity detectors punish second-language writing.
        obs_probs = torch.softmax(obs, dim=-1)
        x_ce = -(obs_probs * torch.log_softmax(perf, dim=-1)).sum(-1).mean()
        x_ppl = x_ce.item()

        if x_ppl <= 0:
            return float("inf")
        return ppl / x_ppl

    def score(self, doc: Document) -> list[AiSignal]:
        if self.calibration is None:
            raise UncalibratedError(
                f"{self.name} has no fitted calibration. Run "
                "scripts/fit_calibration.py against data/eval/ first. Emitting "
                "raw Binoculars ratios as if they were probabilities is the "
                "failure mode this class exists to prevent."
            )
        cal = self.calibration
        out: list[AiSignal] = []
        for span in paragraphs(doc.text):
            passage = doc.text[span.start:span.end]
            raw = self.raw_score(passage)
            p = cal.probability(raw)
            out.append(
                AiSignal(
                    span=span,
                    probability=p,
                    interval=cal.interval(p),
                    fpr_at_threshold=cal.fpr_at_threshold,
                    detector=self.name,
                    raw_score=raw,
                )
            )
        return out


def load_detector(
    calibration_path: str | Path | None = None, **kwargs
) -> AiDetector:
    """Return a Binoculars detector if a calibration exists, else the null one.

    This is the only place the application chooses a detector, so the rule
    "no calibration, no probability" holds everywhere by construction.
    """
    if calibration_path is None:
        return NullAiDetector()
    path = Path(calibration_path)
    if not path.exists():
        return NullAiDetector()
    cal = Calibration.load(path)
    return BinocularsDetector(calibration=cal, **kwargs)
