from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator that retries an async function on failure with exponential backoff."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = kwargs.get("logger") or logging.getLogger("ninova")
            last_exc: Exception | None = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        logger.warning(
                            "%s attempt %d/%d failed: %s – retrying in %.1fs",
                            fn.__name__, attempt, max_attempts, exc, current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            fn.__name__, max_attempts, exc,
                        )

            raise last_exc  # type: ignore[misc]

        return wrapper
    return decorator
