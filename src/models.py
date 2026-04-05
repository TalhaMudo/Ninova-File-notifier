from __future__ import annotations

from pydantic import BaseModel


class FileEntry(BaseModel):
    class_name: str
    file_name: str
    file_url: str
    uploaded_at: str | None = None

    @property
    def unique_key(self) -> str:
        return f"{self.class_name}::{self.file_name}::{self.file_url}"


class GradeEntry(BaseModel):
    class_name: str
    item_name: str
    grade_value: str
    description: str | None = None

    @property
    def unique_key(self) -> str:
        return f"{self.class_name}::{self.item_name}"


class GradeChange(BaseModel):
    class_name: str
    item_name: str
    old_value: str | None = None
    new_value: str
    change_type: str  # "new" | "updated"


class Snapshot(BaseModel):
    fetched_at: str
    files: list[FileEntry] = []
    grades: list[GradeEntry] = []

    def file_keys(self) -> set[str]:
        return {f.unique_key for f in self.files}

    def grade_map(self) -> dict[str, GradeEntry]:
        return {g.unique_key: g for g in self.grades}
