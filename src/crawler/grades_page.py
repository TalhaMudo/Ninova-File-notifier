from __future__ import annotations

import logging

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.config import Settings
from src.crawler.files_page import _extract_class_links  # shared class discovery
from src.models import GradeEntry
from src.utils.debug import save_debug_artifacts


async def collect_all_grades(
    page: Page,
    settings: Settings,
    logger: logging.Logger,
) -> list[GradeEntry]:
    """Navigate each enrolled class and extract rows from the Notlar page."""
    courses_url = f"{settings.ninova_base_url}/Kampus1"
    try:
        await page.goto(courses_url, wait_until="networkidle")
    except PlaywrightTimeout:
        await save_debug_artifacts(page, "grades_courses_navigate", settings, logger)
        raise RuntimeError("Timed out loading course list for grades extraction")

    class_links = await _extract_class_links(page, settings, logger)
    logger.info("Found %d enrolled class(es) for grades extraction", len(class_links))

    all_grades: list[GradeEntry] = []
    for class_name, class_url in class_links:
        logger.info("Checking grades for class: %s", class_name)
        class_grades = await _collect_grades_for_class(page, class_name, class_url, settings, logger)
        all_grades.extend(class_grades)
    return _dedupe_grades(all_grades)


async def _collect_grades_for_class(
    page: Page,
    class_name: str,
    class_url: str,
    settings: Settings,
    logger: logging.Logger,
) -> list[GradeEntry]:
    try:
        await page.goto(class_url, wait_until="networkidle")
    except PlaywrightTimeout:
        logger.warning("Timed out opening class page for grades: %s", class_name)
        return []

    notes_link = await _find_notes_section_link(page)
    if not notes_link:
        logger.info("No Notlar link found for %s", class_name)
        return []

    notes_href = await notes_link.get_attribute("href") or ""
    notes_url = notes_href if notes_href.startswith("http") else f"{settings.ninova_base_url}{notes_href}"

    try:
        await page.goto(notes_url, wait_until="networkidle")
    except PlaywrightTimeout:
        logger.warning("Timed out opening Notlar page for %s", class_name)
        await save_debug_artifacts(page, f"notes_{_slug(class_name)}", settings, logger)
        return []

    return await _extract_grades_from_notes_table(page, class_name)


async def _find_notes_section_link(page: Page):
    keywords = ["notlar", "not", "grades", "grade"]
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


async def _extract_grades_from_notes_table(page: Page, class_name: str) -> list[GradeEntry]:
    grades: list[GradeEntry] = []
    rows = page.locator("table tr")
    row_count = await rows.count()
    if row_count <= 1:
        return grades

    for i in range(1, row_count):
        row = rows.nth(i)
        cells = row.locator("td")
        cell_count = await cells.count()
        if cell_count < 2:
            continue

        item = (await cells.nth(0).inner_text()).strip()
        value = (await cells.nth(1).inner_text()).strip()
        description = (await cells.nth(2).inner_text()).strip() if cell_count >= 3 else ""

        if not item or not value:
            continue
        if _is_noise_grade_row(item, value):
            continue

        grades.append(
            GradeEntry(
                class_name=class_name,
                item_name=item,
                grade_value=value,
                description=description or None,
            )
        )

    return grades


def _is_noise_grade_row(item: str, value: str) -> bool:
    i = item.lower()
    v = value.lower()
    if i in {"dersler", "yardim", "hakkinda", "ninova"}:
        return True
    if "ağırlık ortalamanız" in i:
        return True
    if v in {"not", "açıklama"}:
        return True
    return False


def _dedupe_grades(grades: list[GradeEntry]) -> list[GradeEntry]:
    result: list[GradeEntry] = []
    seen: set[str] = set()
    for grade in grades:
        key = grade.unique_key
        if key in seen:
            continue
        seen.add(key)
        result.append(grade)
    return result


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() or c in {"_", "-"} else "_" for c in value).strip("_")
