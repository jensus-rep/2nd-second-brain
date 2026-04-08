"""Entry schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.core.enums import EntryStatus
from app.schemas.block import BlockRead
from app.schemas.relation import RelationRead


class EntryRead(BaseModel):
    """Full entry with inline blocks and relations — canonical API shape."""
    schema_version: str = "1.0"
    id: str
    title: str
    slug: Optional[str] = None
    category: Optional[str] = None
    status: str
    summary: Optional[str] = None
    blocks: list[BlockRead] = []
    relations: list[RelationRead] = []
    created_at: datetime
    updated_at: datetime


class EntryListItem(BaseModel):
    """Lightweight entry representation for list views."""
    id: str
    title: str
    slug: Optional[str] = None
    category: Optional[str] = None
    status: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EntryCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    category: Optional[str] = None
    status: EntryStatus = EntryStatus.active
    summary: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    status: Optional[EntryStatus] = None
    summary: Optional[str] = None
