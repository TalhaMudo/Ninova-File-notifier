from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models import Snapshot


def load_snapshot(path: str, logger: logging.Logger) -> Snapshot | None:
    """Load the previous snapshot from disk. Returns None on first run."""
    p = Path(path)
    if not p.exists():
        logger.info("No previous snapshot found at %s (first run?)", path)
        return None

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        snapshot = Snapshot.model_validate(data)
        logger.info(
            "Loaded previous snapshot from %s (%d files, fetched at %s)",
            path,
            len(snapshot.files),
            snapshot.fetched_at,
        )
        return snapshot
    except Exception as exc:
        logger.warning("Failed to parse previous snapshot, treating as first run: %s", exc)
        return None


def save_snapshot(snapshot: Snapshot, path: str, logger: logging.Logger) -> None:
    """Persist the current snapshot to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Saved snapshot with %d files to %s", len(snapshot.files), path)
