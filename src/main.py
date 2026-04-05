from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone

from src.config import load_settings
from src.logging_setup import setup_logging
from src.browser.session import new_browser_context
from src.crawler.login import login
from src.crawler.files_page import collect_all_files
from src.crawler.grades_page import collect_all_grades
from src.state.store import load_snapshot, save_snapshot
from src.state.compare import find_grade_changes, find_new_files
from src.notify.bark import send_bark_notification
from src.models import Snapshot


async def run() -> None:
    settings = load_settings()
    secret_values = [settings.ninova_password]
    if settings.bark_device_key:
        secret_values.append(settings.bark_device_key)
    logger = setup_logging(secrets=secret_values)
    logger.info("Starting Ninova file notifier")

    async with new_browser_context(settings) as (browser, context, page):
        logger.info("Logging in to Ninova")
        await login(page, settings, logger)

        logger.info("Collecting files from class pages")
        files = await collect_all_files(page, settings, logger)
        logger.info("Found %d file(s) across all classes", len(files))

        logger.info("Collecting grades from class Notlar pages")
        grades = await collect_all_grades(page, settings, logger)
        logger.info("Found %d grade row(s) across all classes", len(grades))

    current = Snapshot(
        fetched_at=datetime.now(timezone.utc).isoformat(),
        files=files,
        grades=grades,
    )

    previous = load_snapshot(settings.state_file_path, logger)
    first_run = previous is None
    new_files = find_new_files(previous, current)
    grade_changes = find_grade_changes(previous, current)

    if new_files:
        logger.info("Detected %d new file(s)", len(new_files))
        if settings.bark_device_key:
            for file_entry in new_files:
                title = file_entry.class_name
                body = file_entry.file_name
                await send_bark_notification(settings, title, body, logger)
        else:
            logger.info("Bark is not configured, skipping file notification")
    else:
        logger.info("No new files detected")

    if grade_changes:
        logger.info("Detected %d grade change(s)", len(grade_changes))
        if settings.bark_device_key:
            for change in grade_changes:
                title = f"{change.class_name} - {change.item_name}"
                if change.change_type == "new":
                    body = change.new_value
                else:
                    body = f"{change.old_value} -> {change.new_value}"
                await send_bark_notification(settings, title, body, logger)
        else:
            logger.info("Bark is not configured, skipping grade notification")
    else:
        logger.info("No grade changes detected")

    if settings.bark_device_key and first_run and settings.notify_on_first_run:
        await send_bark_notification(
            settings,
            "Ninova monitor initialized",
            f"Baseline created: {len(files)} files, {len(grades)} grades",
            logger,
        )

    if settings.bark_device_key and not new_files and not grade_changes and settings.notify_on_no_updates:
        await send_bark_notification(
            settings,
            "Monkey",
            "No new update found",
            logger,
        )

    save_snapshot(current, settings.state_file_path, logger)
    logger.info("Done")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
