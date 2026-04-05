from __future__ import annotations

import logging
import os
from pathlib import Path

from playwright.async_api import Page

from src.config import Settings


async def save_debug_artifacts(
    page: Page,
    label: str,
    settings: Settings,
    logger: logging.Logger,
) -> None:
    """Save a screenshot and HTML dump for debugging failures."""
    dump_dir = Path("debug_dumps")
    dump_dir.mkdir(exist_ok=True)

    if settings.screenshot_on_failure:
        path = dump_dir / f"{label}.png"
        try:
            await page.screenshot(path=str(path), full_page=True)
            logger.warning("Screenshot saved to %s", path)
        except Exception as exc:
            logger.error("Failed to save screenshot: %s", exc)

    if settings.debug_dump_html:
        path = dump_dir / f"{label}.html"
        try:
            content = await page.content()
            path.write_text(content, encoding="utf-8")
            logger.warning("HTML dump saved to %s", path)
        except Exception as exc:
            logger.error("Failed to save HTML dump: %s", exc)
