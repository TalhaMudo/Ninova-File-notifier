from __future__ import annotations

import logging

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout


async def wait_for_any_selector(
    page: Page,
    selectors: list[str],
    timeout_ms: int = 10_000,
    logger: logging.Logger | None = None,
) -> str | None:
    """Wait until at least one of the given selectors appears on the page.

    Returns the first matching selector, or None if none matched within timeout.
    """
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=timeout_ms // len(selectors))
            return sel
        except PlaywrightTimeout:
            continue

    if logger:
        logger.warning("None of the selectors appeared within %dms: %s", timeout_ms, selectors)
    return None


async def wait_for_page_ready(page: Page, timeout_ms: int = 15_000) -> None:
    """Wait until the page appears fully loaded (networkidle + domcontentloaded)."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeout:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
