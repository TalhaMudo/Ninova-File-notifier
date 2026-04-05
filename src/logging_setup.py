from __future__ import annotations

import logging
import re
import sys


class SecretFilter(logging.Filter):
    """Redacts known secret patterns from log records."""

    def __init__(self, secrets: list[str] | None = None) -> None:
        super().__init__()
        self._secrets = [s for s in (secrets or []) if s]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for secret in self._secrets:
            msg = msg.replace(secret, "***")
        record.msg = msg
        record.args = None
        return True


def setup_logging(secrets: list[str] | None = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("ninova")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
        handler.addFilter(SecretFilter(secrets))
        logger.addHandler(handler)

    return logger
