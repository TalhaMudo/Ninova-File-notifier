from __future__ import annotations

import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ninova_username: str
    ninova_password: str
    bark_device_key: str | None = None
    bark_base_url: str = "https://api.day.app"
    bark_icon_url: str | None = None
    ninova_base_url: str = "https://ninova.itu.edu.tr"
    state_file_path: str = "state/latest_snapshot.json"
    headless: bool = True
    screenshot_on_failure: bool = True
    debug_dump_html: bool = True
    request_timeout_ms: int = 30_000
    navigation_timeout_ms: int = 60_000
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    notify_on_first_run: bool = True
    notify_on_no_updates: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:
        print(f"[FATAL] Failed to load settings – are all required env vars set?\n{exc}", file=sys.stderr)
        sys.exit(1)
