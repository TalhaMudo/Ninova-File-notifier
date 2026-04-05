from __future__ import annotations

from src.models import FileEntry, Snapshot


def find_new_files(previous: Snapshot | None, current: Snapshot) -> list[FileEntry]:
    """Compare two snapshots and return files present in current but not previous.

    On first run (previous is None), we treat all files as "already known"
    to avoid a notification flood.
    """
    if previous is None:
        return []

    old_keys = previous.file_keys()
    return [f for f in current.files if f.unique_key not in old_keys]
