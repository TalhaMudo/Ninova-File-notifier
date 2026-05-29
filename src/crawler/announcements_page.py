from __future__ import annotations

import logging
import re

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.config import Settings
from src.crawler.files_page import _extract_class_links  # shared class discovery
from src.models import AnnouncementEntry
from src.utils.debug import save_debug_artifacts


async def collect_all_announcements(
    page: Page,
    settings: Settings,
    logger: logging.Logger,
) -> list[AnnouncementEntry]:
    """Navigate each enrolled class and extract announcement entries from Duyurular pages."""
    courses_url = f"{settings.ninova_base_url}/Kampus1"
    try:
        await page.goto(courses_url, wait_until="networkidle")
    except PlaywrightTimeout:
        await save_debug_artifacts(page, "announcements_courses_navigate", settings, logger)
        raise RuntimeError("Timed out loading course list for announcements extraction")

    class_links = await _extract_class_links(page, settings, logger)
    logger.info("Found %d enrolled class(es) for announcements extraction", len(class_links))

    all_announcements: list[AnnouncementEntry] = []
    for class_name, class_url in class_links:
        logger.info("Checking announcements for class: %s", class_name)
        class_announcements = await _collect_announcements_for_class(
            page, class_name, class_url, settings, logger
        )
        all_announcements.extend(class_announcements)
    return _dedupe_announcements(all_announcements)


async def _collect_announcements_for_class(
    page: Page,
    class_name: str,
    class_url: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[AnnouncementEntry]:
    try:
        await page.goto(class_url, wait_until="networkidle")
    except PlaywrightTimeout:
        logger.warning("Timed out opening class page for announcements: %s", class_name)
        return []

    announcements_link = await _find_announcements_section_link(page)
    if not announcements_link:
        logger.info("No Duyurular link found for %s", class_name)
        return []

    ann_href = await announcements_link.get_attribute("href") or ""
    ann_url = ann_href if ann_href.startswith("http") else f"{settings.ninova_base_url}{ann_href}"

    try:
        await page.goto(ann_url, wait_until="networkidle")
    except PlaywrightTimeout:
        logger.warning("Timed out opening Duyurular page for %s", class_name)
        await save_debug_artifacts(page, f"announcements_{_slug(class_name)}", settings, logger)
        return []

    return await _extract_announcements_from_page(page, class_name, settings.ninova_base_url)


async def _find_announcements_section_link(page: Page):
    """Find the sidebar/nav link to the Duyurular (announcements) section."""
    keywords = ["duyuru", "duyurular", "announcement", "announcements"]
    nav_links = page.locator("a[href]")
    count = await nav_links.count()
    for i in range(count):
        el = nav_links.nth(i)
        text = (await el.inner_text()).strip().lower()
        href = (await el.get_attribute("href") or "").strip().lower()
        if any(k in text for k in keywords) or any(k in href for k in keywords):
            if "/sinif/" in href:
                return el
    return None


async def _extract_announcements_from_page(
    page: Page,
    class_name: str,
    base_url: str,
) -> list[AnnouncementEntry]:
    announcements: list[AnnouncementEntry] = []
    seen_urls: set[str] = set()

    # Primary: row-based extraction from table layout
    rows = page.locator("table tr")
    row_count = await rows.count()
    if row_count > 1:
        for i in range(row_count):
            row = rows.nth(i)
            link = row.locator("a").first
            if await link.count() == 0:
                continue
            href = (await link.get_attribute("href") or "").strip()
            title = (await link.inner_text()).strip()
            if not href or not title:
                continue
            if not _is_announcement_detail_link(href):
                continue
            full_url = href if href.startswith("http") else f"{base_url}{href}"
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            posted_at = None
            cells = row.locator("td")
            cell_count = await cells.count()
            if cell_count >= 2:
                date_text = (await cells.nth(cell_count - 1).inner_text()).strip()
                if _looks_like_date(date_text):
                    posted_at = date_text

            announcements.append(AnnouncementEntry(
                class_name=class_name,
                title=title,
                url=full_url,
                posted_at=posted_at,
            ))
        if announcements:
            return announcements

    # Fallback: any individual announcement links on the page
    links = page.locator("a[href]")
    count = await links.count()
    for i in range(count):
        el = links.nth(i)
        href = (await el.get_attribute("href") or "").strip()
        title = (await el.inner_text()).strip()
        if not href or not title:
            continue
        if not _is_announcement_detail_link(href):
            continue
        full_url = href if href.startswith("http") else f"{base_url}{href}"
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        announcements.append(AnnouncementEntry(
            class_name=class_name,
            title=title,
            url=full_url,
        ))

    return announcements


def _is_announcement_detail_link(href: str) -> bool:
    """True only for individual announcement URLs (not the section landing page).

    Section page:       /Sinif/{id}/Duyurular        (plural, no trailing number)
    Individual post:    /Sinif/{id}/Duyuru/{number}  (singular + numeric ID)
    """
    return bool(re.search(r"/Sinif/[^/]+/Duyuru/\d+", href, re.IGNORECASE))


def _looks_like_date(text: str) -> bool:
    if not text:
        return False
    digit_count = sum(c.isdigit() for c in text)
    has_sep = any(c in text for c in ".-/")
    return digit_count >= 4 and has_sep


def _dedupe_announcements(announcements: list[AnnouncementEntry]) -> list[AnnouncementEntry]:
    result: list[AnnouncementEntry] = []
    seen: set[str] = set()
    for ann in announcements:
        key = ann.unique_key
        if key in seen:
            continue
        seen.add(key)
        result.append(ann)
    return result


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() or c in {"_", "-"} else "_" for c in value).strip("_")
