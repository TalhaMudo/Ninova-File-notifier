from __future__ import annotations

import logging

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.config import Settings
from src.crawler.extractors import extract_files_from_page
from src.models import FileEntry
from src.utils.debug import save_debug_artifacts


async def collect_all_files(
    page: Page,
    settings: Settings,
    logger: logging.Logger,
) -> list[FileEntry]:
    """Navigate to each enrolled class and collect file metadata.

    Flow:
        1. Go to the Ninova main page (course list).
        2. Extract links to each enrolled class.
        3. For each class, navigate to its "Sinif Dosyalari" / files section.
        4. Extract all file entries.
    """
    courses_url = f"{settings.ninova_base_url}/Kampus1"
    logger.info("Navigating to course list: %s", courses_url)

    try:
        await page.goto(courses_url, wait_until="networkidle")
    except PlaywrightTimeout:
        await save_debug_artifacts(page, "courses_navigate", settings, logger)
        raise RuntimeError("Timed out loading the course list page")

    class_links = await _extract_class_links(page, settings, logger)
    logger.info("Found %d enrolled class(es)", len(class_links))

    all_files: list[FileEntry] = []

    for class_name, class_url in class_links:
        logger.info("Processing class: %s", class_name)
        files = await _collect_files_for_class(page, class_name, class_url, settings, logger)
        all_files.extend(files)

    return all_files


async def _extract_class_links(
    page: Page,
    settings: Settings,
    logger: logging.Logger,
) -> list[tuple[str, str]]:
    """Return list of (class_name, class_url) from the dashboard / course list."""
    # Ninova typically lists classes with links inside elements on the main dashboard.
    # Selectors target the most common patterns; will be refined during testing.
    selectors = [
        "a.courseLink",
        "td.courseInfo a",
        ".courseName a",
        "#mainContent a[href*='/EKampus/']",
        "#mainContent a[href*='/Kampus1/']",
        "a[href*='/Ders/']",
    ]

    links: list[tuple[str, str]] = []

    for sel in selectors:
        elements = page.locator(sel)
        count = await elements.count()
        if count > 0:
            for i in range(count):
                el = elements.nth(i)
                text = (await el.inner_text()).strip()
                href = await el.get_attribute("href") or ""
                if href and text:
                    full_url = href if href.startswith("http") else f"{settings.ninova_base_url}{href}"
                    links.append((text, full_url))
            break

    if not links:
        await save_debug_artifacts(page, "no_class_links", settings, logger)
        logger.warning("No class links found – page structure may have changed")

    return links


async def _collect_files_for_class(
    page: Page,
    class_name: str,
    class_url: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[FileEntry]:
    """Navigate to a class's files/notes section and extract file entries."""
    try:
        await page.goto(class_url, wait_until="networkidle")
    except PlaywrightTimeout:
        logger.error("Timed out loading class page: %s", class_url)
        await save_debug_artifacts(page, f"class_{class_name}_navigate", settings, logger)
        return []

    files_link = await _find_files_section_link(page)
    if not files_link:
        logger.info("No files/notes section found for %s", class_name)
        return []

    files_url = await files_link.get_attribute("href") or ""
    full_files_url = files_url if files_url.startswith("http") else f"{settings.ninova_base_url}{files_url}"

    try:
        await page.goto(full_files_url, wait_until="networkidle")
    except PlaywrightTimeout:
        logger.error("Timed out loading files page for %s", class_name)
        await save_debug_artifacts(page, f"class_{class_name}_files", settings, logger)
        return []

    return await extract_files_from_page(page, class_name, settings, logger)


async def _find_files_section_link(page: Page):
    """Look for the navigation link to 'Sinif Dosyalari' or equivalent."""
    files_keywords = ["dosya", "sinif dosyalari", "ders dosyalari", "files", "resources", "belgeler"]

    # Try sidebar/nav links first
    nav_links = page.locator("nav a, .sidebar a, .menu a, #leftMenu a, .nav a")
    count = await nav_links.count()
    for i in range(count):
        el = nav_links.nth(i)
        text = (await el.inner_text()).strip().lower()
        for keyword in files_keywords:
            if keyword in text:
                return el

    # Fallback: any link on page
    all_links = page.locator("a")
    count = await all_links.count()
    for i in range(count):
        el = all_links.nth(i)
        text = (await el.inner_text()).strip().lower()
        href = (await el.get_attribute("href") or "").lower()
        for keyword in files_keywords:
            if keyword in text or keyword in href:
                return el

    return None
