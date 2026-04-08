"""Snapshot schemas for full-state export/import."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel
from app.schemas.entry import EntryRead
from app.schemas.view import ViewRead


class SnapshotExport(BaseModel):
    schema_version: str = "1.0"
    exported_at: datetime
    entries: list[EntryRead] = []
    views: list[ViewRead] = []


class SnapshotImportResult(BaseModel):
    schema_version: str = "1.0"
    imported_at: datetime
    created_entries: int = 0
    updated_entries: int = 0
    created_views: int = 0
    updated_views: int = 0
    errors: list[str] = []
