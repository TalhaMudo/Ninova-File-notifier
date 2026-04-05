from __future__ import annotations

from src.models import FileEntry, GradeChange, Snapshot


def find_new_files(previous: Snapshot | None, current: Snapshot) -> list[FileEntry]:
    """Compare two snapshots and return files present in current but not previous.

    On first run (previous is None), we treat all files as "already known"
    to avoid a notification flood.
    """
    if previous is None:
        return []

    old_keys = previous.file_keys()
    return [f for f in current.files if f.unique_key not in old_keys]


def find_grade_changes(previous: Snapshot | None, current: Snapshot) -> list[GradeChange]:
    """Return new and updated grade rows for all classes.

    On first run, no grade change is returned to avoid noise.
    """
    if previous is None:
        return []

    previous_map = previous.grade_map()
    current_map = current.grade_map()

    changes: list[GradeChange] = []

    for key, current_grade in current_map.items():
        old_grade = previous_map.get(key)
        if old_grade is None:
            changes.append(
                GradeChange(
                    class_name=current_grade.class_name,
                    item_name=current_grade.item_name,
                    old_value=None,
                    new_value=current_grade.grade_value,
                    change_type="new",
                )
            )
            continue

        if old_grade.grade_value != current_grade.grade_value:
            changes.append(
                GradeChange(
                    class_name=current_grade.class_name,
                    item_name=current_grade.item_name,
                    old_value=old_grade.grade_value,
                    new_value=current_grade.grade_value,
                    change_type="updated",
                )
            )

    return changes
