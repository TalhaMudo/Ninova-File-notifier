from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

from src.config import Settings


async def send_bark_notification(
    settings: Settings,
    title: str,
    body: str,
    logger: logging.Logger,
) -> None:
    """Send a push notification via Bark path format.

    Format:
      GET {base_url}/{device_key}/{title}/{body}?icon={icon_url}
    """
    if not settings.bark_device_key:
        logger.info("Bark device key is missing, skipping notification")
        return

    encoded_title = quote(title, safe="")
    encoded_body = quote(body, safe="")
    base = settings.bark_base_url.rstrip("/")
    url = f"{base}/{settings.bark_device_key}/{encoded_title}/{encoded_body}"
    params: dict[str, str] = {}
    if settings.bark_icon_url:
        params["icon"] = settings.bark_icon_url

    logger.info("Sending Bark notification: %s", title)

    last_error: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
            logger.info("Bark notification sent successfully")
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Bark attempt %d/%d failed: %s", attempt, settings.max_retries, exc)

    logger.error("All Bark notification attempts failed. Last error: %s", last_error)
