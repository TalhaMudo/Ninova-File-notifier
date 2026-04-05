from __future__ import annotations

import logging

import httpx

from src.config import Settings


async def send_bark_notification(
    settings: Settings,
    title: str,
    body: str,
    logger: logging.Logger,
) -> None:
    """Send a push notification via the Bark API.

    Bark endpoint format: POST {base_url}/{device_key}
    JSON payload: {"title": ..., "body": ..., "group": ..., "sound": ...}
    """
    url = f"{settings.bark_base_url}/{settings.bark_device_key}"
    payload = {
        "title": title,
        "body": body,
        "group": "Ninova",
        "sound": "minuet",
        "isArchive": 1,
    }

    logger.info("Sending Bark notification: %s", title)

    last_error: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            logger.info("Bark notification sent successfully")
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Bark attempt %d/%d failed: %s", attempt, settings.max_retries, exc)

    logger.error("All Bark notification attempts failed. Last error: %s", last_error)
