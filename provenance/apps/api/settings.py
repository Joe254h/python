"""Configuration, read once from the environment.

Defaults are chosen so that `python -m apps.api.main` with no environment at
all starts a working application: SQLite in ./data, the real detector, no AI
detection (because no calibration is fitted yet), and mock mode off.

`use_mock_detector` is the one setting that can produce output which looks real
and is not, so it is loud everywhere -- it forces a banner in the UI, stamps
`is_mock` on every report, and is printed at startup. The plan's rule is that
no number produced by the mock is ever shown outside a dev build, and that rule
is enforced here rather than remembered.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    db_path: str = field(
        default_factory=lambda: os.environ.get(
            "PROVENANCE_DB", str(ROOT / "data" / "provenance.db")
        )
    )
    corpus_path: str = field(
        default_factory=lambda: os.environ.get(
            "PROVENANCE_CORPUS", str(ROOT / "data" / "corpus.db")
        )
    )
    upload_dir: str = field(
        default_factory=lambda: os.environ.get(
            "PROVENANCE_UPLOADS", str(ROOT / "data" / "uploads")
        )
    )
    #: Path to a fitted AI-detection calibration. Absent means AI detection
    #: does not run, which is the correct default -- see aidetect.Calibration.
    calibration_path: str | None = field(
        default_factory=lambda: os.environ.get("PROVENANCE_CALIBRATION")
    )
    use_mock_detector: bool = field(
        default_factory=lambda: _bool("PROVENANCE_DEMO_MODE", False)
    )
    mock_stage_delay_s: float = field(
        default_factory=lambda: float(os.environ.get("PROVENANCE_MOCK_DELAY", "0"))
    )
    max_upload_mb: int = field(
        default_factory=lambda: int(os.environ.get("PROVENANCE_MAX_UPLOAD_MB", "20"))
    )
    secure_cookies: bool = field(
        default_factory=lambda: _bool("PROVENANCE_SECURE_COOKIES", False)
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def banner(self) -> str:
        lines = [
            f"  database    {self.db_path}",
            f"  corpus      {self.corpus_path}",
            f"  uploads     {self.upload_dir}",
            f"  ai detector {self.calibration_path or 'not configured (will not run)'}",
        ]
        if self.use_mock_detector:
            lines.append(
                "  DEMO MODE   ON - reports are FABRICATED and marked as such"
            )
        return "\n".join(lines)
