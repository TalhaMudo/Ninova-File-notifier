from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone

from src.config import load_settings
from src.logging_setup import setup_logging
from src.browser.session import new_browser_context
from src.crawler.login import login
from src.crawler.files_page import collect_all_files
from src.state.store import load_snapshot, save_snapshot
from src.state.compare import find_new_files
from src.notify.bark import send_bark_notification
from src.notify.message_builder import build_message
from src.models import Snapshot


async def run() -> None:
    settings = load_settings()
    logger = setup_logging(secrets=[settings.ninova_password, settings.bark_device_key])
    logger.info("Starting Ninova file notifier")

    async with new_browser_context(settings) as (browser, context, page):
        logger.info("Logging in to Ninova")
        await login(page, settings, logger)

        logger.info("Collecting files from class pages")
        files = await collect_all_files(page, settings, logger)
        logger.info("Found %d file(s) across all classes", len(files))

    current = Snapshot(
        fetched_at=datetime.now(timezone.utc).isoformat(),
        files=files,
    )

    previous = load_snapshot(settings.state_file_path, logger)
    new_files = find_new_files(previous, current)

    if new_files:
        logger.info("Detected %d new file(s)", len(new_files))
        title, body = build_message(new_files)
        await send_bark_notification(settings, title, body, logger)
    else:
        logger.info("No new files detected")

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
