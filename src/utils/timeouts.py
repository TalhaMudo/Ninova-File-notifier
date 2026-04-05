from __future__ import annotations

from playwright.async_api import Page

from src.config import Settings


async def configure_page_timeouts(page: Page, settings: Settings) -> None:
    """Apply consistent timeout settings to a Playwright page."""
    page.set_default_timeout(settings.request_timeout_ms)
    page.set_default_navigation_timeout(settings.navigation_timeout_ms)
