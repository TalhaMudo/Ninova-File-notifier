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


class Snapshot(BaseModel):
    fetched_at: str
    files: list[FileEntry] = []

    def file_keys(self) -> set[str]:
        return {f.unique_key for f in self.files}
