from __future__ import annotations

import logging
import re

from playwright.async_api import Page

from src.config import Settings
from src.models import FileEntry


async def extract_files_from_page(
    page: Page,
    class_name: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[FileEntry]:
    """Extract file entries recursively from Ninova class file folders."""
    visited: set[str] = set()
    start_url = page.url
    files = await _crawl_directory(
        page=page,
        class_name=class_name,
        settings=settings,
        logger=logger,
        directory_url=start_url,
        folder_stack=[],
        visited=visited,
    )
    if not files:
        logger.info("No files found on page for %s (may be empty)", class_name)
    return files


async def _crawl_directory(
    page: Page,
    class_name: str,
    settings: Settings,
    logger: logging.Logger,
    directory_url: str,
    folder_stack: list[str],
    visited: set[str],
) -> list[FileEntry]:
    """Recursively walk one class's SinifDosyalari listing."""
    normalized_dir = _normalize_url(directory_url)
    if normalized_dir in visited:
        return []
    visited.add(normalized_dir)

    if _normalize_url(page.url) != normalized_dir:
        await page.goto(directory_url, wait_until="networkidle")

    # Primary strategy: row-based extraction from the "Sinif Dosyalari" table
    files: list[FileEntry] = []
    rows = page.locator("table tr")
    count = await rows.count()
    if count <= 1:
        # Fallback for unexpected layout
        return await _extract_from_links(page, class_name, settings, logger, folder_stack)

    for i in range(1, count):  # skip header row
        row = rows.nth(i)
        link = row.locator("a").first
        if await link.count() == 0:
            continue

        file_name = (await link.inner_text()).strip()
        href = await link.get_attribute("href") or ""
        if not file_name or not href:
            continue
        if _is_noise_navigation_link(file_name, href):
            continue

        full_url = href if href.startswith("http") else f"{settings.ninova_base_url}{href}"
        if not _is_class_file_link(full_url):
            continue

        icon_src = await _row_icon_src(row)
        is_folder = "folder" in icon_src.lower()

        if is_folder:
            logger.info("Entering folder %s for %s", file_name, class_name)
            nested = await _crawl_directory(
                page=page,
                class_name=class_name,
                settings=settings,
                logger=logger,
                directory_url=full_url,
                folder_stack=[*folder_stack, file_name],
                visited=visited,
            )
            files.extend(nested)
            continue

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
            file_name=_with_folder_prefix(folder_stack, file_name),
            file_url=full_url,
            uploaded_at=uploaded_at,
        ))

    return files


async def _extract_from_links(
    page: Page,
    class_name: str,
    settings: Settings,
    logger: logging.Logger,
    folder_stack: list[str] | None = None,
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
        if _is_noise_navigation_link(text, href):
            continue

        full_url = href if href.startswith("http") else f"{settings.ninova_base_url}{href}"
        files.append(FileEntry(
            class_name=class_name,
            file_name=_with_folder_prefix(folder_stack or [], text),
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


def _is_noise_navigation_link(name: str, href: str) -> bool:
    n = name.strip().lower()
    h = href.strip().lower()
    if "/tr/dersler" in h:
        return True
    if "javascript:__dopostback" in h:
        return True
    if "?u0" in h:
        return True
    if "ana dizin" in n or "üst dizin" in n or "ust dizin" in n:
        return True
    if n in {"dersler", "yardim", "hakkinda", "ninova"}:
        return True
    return False


async def _row_icon_src(row) -> str:
    icon = row.locator("img").first
    if await icon.count() == 0:
        return ""
    return (await icon.get_attribute("src") or "").strip()


def _with_folder_prefix(folder_stack: list[str], file_name: str) -> str:
    if not folder_stack:
        return file_name
    return "/".join([*folder_stack, file_name])


def _is_class_file_link(url: str) -> bool:
    url_lower = url.lower()
    # Keep only class files listing links (root or folder links via ?g...)
    return "/sinif/" in url_lower and "/sinifdosyalari" in url_lower


def _normalize_url(url: str) -> str:
    return re.sub(r"(?<=\?)$", "", url.strip())
