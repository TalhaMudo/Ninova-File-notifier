from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.config import Settings


@asynccontextmanager
async def new_browser_context(
    settings: Settings,
) -> AsyncGenerator[tuple[Browser, BrowserContext, Page], None]:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=settings.headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        context.set_default_timeout(settings.request_timeout_ms)
        context.set_default_navigation_timeout(settings.navigation_timeout_ms)
        page = await context.new_page()
        try:
            yield browser, context, page
        finally:
            await context.close()
            await browser.close()
