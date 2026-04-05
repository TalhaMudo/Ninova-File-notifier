from __future__ import annotations

from collections import defaultdict

from src.models import FileEntry, GradeChange


def build_message(new_files: list[FileEntry]) -> tuple[str, str]:
    """Build a concise Bark notification title and body from new file entries.

    Returns (title, body).
    """
    count = len(new_files)
    title = f"Ninova: {count} new file{'s' if count != 1 else ''} uploaded"

    grouped: dict[str, list[FileEntry]] = defaultdict(list)
    for f in new_files:
        grouped[f.class_name].append(f)

    lines: list[str] = []
    for class_name, files in grouped.items():
        lines.append(f"[{class_name}]")
        for f in files:
            date_suffix = f" ({f.uploaded_at})" if f.uploaded_at else ""
            lines.append(f"  - {f.file_name}{date_suffix}")

    body = "\n".join(lines)
    return title, body


def build_grade_message(grade_changes: list[GradeChange]) -> tuple[str, str]:
    """Build Bark title/body for grade changes."""
    count = len(grade_changes)
    title = f"Ninova: {count} grade update{'s' if count != 1 else ''}"

    grouped: dict[str, list[GradeChange]] = defaultdict(list)
    for change in grade_changes:
        grouped[change.class_name].append(change)

    lines: list[str] = []
    for class_name, changes in grouped.items():
        lines.append(f"[{class_name}]")
        for c in changes:
            if c.change_type == "new":
                lines.append(f"  - New: {c.item_name} = {c.new_value}")
            else:
                lines.append(f"  - Updated: {c.item_name} {c.old_value} -> {c.new_value}")

    body = "\n".join(lines)
    return title, body
