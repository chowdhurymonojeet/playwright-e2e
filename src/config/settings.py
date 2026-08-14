from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    environment_name: str
    base_url: str
    api_base_url: str
    auth_base_url: str
    db_dsn: str
    api_token: str | None
    ui_username: str | None
    ui_password: str | None
    browser_name: str
    headless: bool
    api_timeout_seconds: float
    artifacts_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            environment_name=os.getenv("CG_ENVIRONMENT", "local"),
            base_url=os.getenv("CG_BASE_URL", "http://localhost:3000"),
            api_base_url=os.getenv("CG_API_BASE_URL", "http://localhost:8000"),
            auth_base_url=os.getenv("CG_AUTH_BASE_URL", "http://localhost:8000"),
            db_dsn=os.getenv("CG_DB_DSN", ""),
            api_token=os.getenv("CG_API_TOKEN") or None,
            ui_username=os.getenv("CG_UI_USERNAME") or None,
            ui_password=os.getenv("CG_UI_PASSWORD") or None,
            browser_name=os.getenv("CG_BROWSER_NAME", "chromium"),
            headless=_read_bool("CG_HEADLESS", True),
            api_timeout_seconds=float(os.getenv("CG_API_TIMEOUT_SECONDS", "15")),
            artifacts_dir=Path(os.getenv("CG_ARTIFACTS_DIR", "artifacts")),
        )
