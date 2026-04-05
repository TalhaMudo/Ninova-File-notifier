from __future__ import annotations

import logging
import os
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.config import Settings
from src.utils.debug import save_debug_artifacts


async def login(page: Page, settings: Settings, logger: logging.Logger) -> None:
    """Log in to Ninova through ITU's CAS/SSO gate.

    ITU uses a central authentication page that redirects back to Ninova after
    successful login.  The flow is:
        1. Navigate to Ninova → redirected to giris.itu.edu.tr (or CAS)
        2. Fill username + password
        3. Submit the form
        4. Wait for redirect back to Ninova dashboard
    """
    login_url = f"{settings.ninova_base_url}/Kampus1"
    logger.info("Navigating to %s", login_url)

    try:
        await page.goto(login_url, wait_until="networkidle")
    except PlaywrightTimeout:
        await save_debug_artifacts(page, "login_navigate", settings, logger)
        raise RuntimeError("Timed out navigating to the login page")

    current = page.url
    logger.info("Landed on %s", current)

    # If we're already on Ninova dashboard, session might be cached
    if _is_ninova_dashboard(current):
        logger.info("Already authenticated – skipping login form")
        return

    # Fill the login form
    try:
        await _fill_and_submit(page, settings, logger)
    except Exception:
        await save_debug_artifacts(page, "login_submit", settings, logger)
        raise

    # Wait for redirect back to Ninova
    try:
        await page.wait_for_url(f"{settings.ninova_base_url}/**", timeout=settings.navigation_timeout_ms)
    except PlaywrightTimeout:
        await save_debug_artifacts(page, "login_redirect", settings, logger)
        raise RuntimeError("Login succeeded but redirect back to Ninova timed out")

    if not _is_ninova_dashboard(page.url):
        await save_debug_artifacts(page, "login_unexpected_landing", settings, logger)
        raise RuntimeError(f"Unexpected post-login page: {page.url}")

    logger.info("Login successful – on dashboard: %s", page.url)


async def _fill_and_submit(page: Page, settings: Settings, logger: logging.Logger) -> None:
    """Locate username/password fields and submit.

    Ninova's SSO page has historically used different input names.  We try
    several common selectors to be resilient.
    """
    username_selectors = ["input[name='username']", "input[name='loginUsername']", "#username", "input[type='text']"]
    password_selectors = ["input[name='password']", "input[name='loginPassword']", "#password", "input[type='password']"]

    username_el = await _find_first(page, username_selectors)
    password_el = await _find_first(page, password_selectors)

    if not username_el or not password_el:
        raise RuntimeError("Could not locate username/password fields on the login page")

    await username_el.fill(settings.ninova_username)
    await password_el.fill(settings.ninova_password)
    logger.info("Credentials entered, submitting form")

    submit_selectors = ["button[type='submit']", "input[type='submit']", "#submitButton", "button.btn-primary"]
    submit_el = await _find_first(page, submit_selectors)
    if submit_el:
        await submit_el.click()
    else:
        await password_el.press("Enter")

    await page.wait_for_load_state("networkidle")


async def _find_first(page: Page, selectors: list[str]):
    for sel in selectors:
        el = page.locator(sel).first
        if await el.count() > 0:
            return el
    return None


def _is_ninova_dashboard(url: str) -> bool:
    url_lower = url.lower()
    return "ninova.itu.edu.tr" in url_lower and "giris" not in url_lower and "login" not in url_lower
