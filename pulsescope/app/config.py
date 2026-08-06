"""Runtime configuration, loaded from environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def _bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # --- credentials (all optional; an actor without its key stays dormant) ---
    x_bearer_token: str = field(default_factory=lambda: os.getenv("X_BEARER_TOKEN", ""))
    youtube_api_key: str = field(default_factory=lambda: os.getenv("YOUTUBE_API_KEY", ""))
    meta_access_token: str = field(default_factory=lambda: os.getenv("META_ACCESS_TOKEN", ""))
    tiktok_access_token: str = field(default_factory=lambda: os.getenv("TIKTOK_ACCESS_TOKEN", ""))
    serper_api_key: str = field(default_factory=lambda: os.getenv("SERPER_API_KEY", ""))
    brave_api_key: str = field(default_factory=lambda: os.getenv("BRAVE_API_KEY", ""))
    reddit_client_id: str = field(default_factory=lambda: os.getenv("REDDIT_CLIENT_ID", ""))
    reddit_client_secret: str = field(default_factory=lambda: os.getenv("REDDIT_CLIENT_SECRET", ""))

    # --- behaviour ---
    demo_mode: bool = field(default_factory=lambda: _bool("PULSESCOPE_DEMO", False))
    region: str = field(default_factory=lambda: os.getenv("PULSESCOPE_REGION", "KE"))
    language: str = field(default_factory=lambda: os.getenv("PULSESCOPE_LANG", "en"))
    lookback_days: int = field(default_factory=lambda: _int("PULSESCOPE_LOOKBACK_DAYS", 90))
    max_items_per_actor: int = field(default_factory=lambda: _int("PULSESCOPE_MAX_ITEMS", 60))
    concurrency: int = field(default_factory=lambda: _int("PULSESCOPE_CONCURRENCY", 8))
    request_timeout: int = field(default_factory=lambda: _int("PULSESCOPE_TIMEOUT", 25))
    cache_ttl: int = field(default_factory=lambda: _int("PULSESCOPE_CACHE_TTL", 900))
    user_agent: str = field(
        default_factory=lambda: os.getenv(
            "PULSESCOPE_UA",
            "Mozilla/5.0 (compatible; PulseScope/1.0; +https://github.com/joe254h/python)",
        )
    )

    @property
    def data_dir(self) -> Path:
        d = Path(os.getenv("PULSESCOPE_DATA_DIR", ROOT / "data"))
        d.mkdir(parents=True, exist_ok=True)
        return d


settings = Settings()
