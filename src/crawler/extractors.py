from __future__ import annotations

import logging

from playwright.async_api import Page

from src.config import Settings
from src.models import FileEntry
from src.utils.debug import save_debug_artifacts


async def extract_files_from_page(
    page: Page,
    class_name: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[FileEntry]:
    """Extract file entries from a Ninova class files page.

    Ninova typically renders files inside a table or a list with download links.
    We try several common structures and fall back gracefully.
    """
    files: list[FileEntry] = []

    # Strategy 1: table rows with download links
    rows = page.locator("table tr")
    row_count = await rows.count()
    if row_count > 1:
        files = await _extract_from_table(page, class_name, settings, logger)

    # Strategy 2: list items or divs with file links
    if not files:
        files = await _extract_from_links(page, class_name, settings, logger)

    if not files:
        logger.info("No files found on page for %s (may be empty)", class_name)

    return files


async def _extract_from_table(
    page: Page,
    class_name: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[FileEntry]:
    """Extract file info from a table-based layout."""
    files: list[FileEntry] = []
    rows = page.locator("table tr")
    count = await rows.count()

    for i in range(1, count):  # skip header row
        row = rows.nth(i)
        link = row.locator("a").first
        if await link.count() == 0:
            continue

        file_name = (await link.inner_text()).strip()
        href = await link.get_attribute("href") or ""
        if not file_name or not href:
            continue

        full_url = href if href.startswith("http") else f"{settings.ninova_base_url}{href}"

        # Try to grab an upload date from the row
        cells = row.locator("td")
        uploaded_at = None
        cell_count = await cells.count()
        if cell_count >= 2:
            date_text = (await cells.nth(cell_count - 1).inner_text()).strip()
            if _looks_like_date(date_text):
                uploaded_at = date_text

        files.append(FileEntry(
            class_name=class_name,
            file_name=file_name,
            file_url=full_url,
            uploaded_at=uploaded_at,
        ))

    return files


async def _extract_from_links(
    page: Page,
    class_name: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[FileEntry]:
    """Fallback: extract any downloadable-looking links on the page."""
    files: list[FileEntry] = []
    file_extensions = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".zip", ".rar", ".txt", ".csv")

    links = page.locator("a[href]")
    count = await links.count()
    for i in range(count):
        el = links.nth(i)
        href = (await el.get_attribute("href") or "").strip()
        text = (await el.inner_text()).strip()
        if not href or not text:
            continue

        href_lower = href.lower()
        is_file = any(href_lower.endswith(ext) for ext in file_extensions) or "download" in href_lower
        if not is_file:
            continue

        full_url = href if href.startswith("http") else f"{settings.ninova_base_url}{href}"
        files.append(FileEntry(
            class_name=class_name,
            file_name=text,
            file_url=full_url,
        ))

    return files


def _looks_like_date(text: str) -> bool:
    """Rough heuristic: contains digits and date-ish separators."""
    if not text:
        return False
    digit_count = sum(c.isdigit() for c in text)
    has_sep = any(c in text for c in ".-/")
    return digit_count >= 4 and has_sep
