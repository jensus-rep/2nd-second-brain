"""View and ViewItem schemas."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel
from app.core.enums import ViewType


class ViewItemRead(BaseModel):
    id: str
    entry_id: str
    position: int
    section_label: Optional[str] = None
    created_at: datetime


class ViewItemCreate(BaseModel):
    entry_id: str
    position: int = 0
    section_label: Optional[str] = None


class ViewItemReorderRequest(BaseModel):
    """item_ids must be the complete ordered list of all ViewItem IDs for the view."""
    item_ids: list[str]


class ViewRead(BaseModel):
    schema_version: str = "1.0"
    id: str
    title: str
    description: Optional[str] = None
    type: str
    filter: Optional[dict[str, Any]] = None
    sort: Optional[dict[str, Any]] = None
    items: list[ViewItemRead] = []
    created_at: datetime
    updated_at: datetime


class ViewListItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: str
    created_at: datetime
    updated_at: datetime


class ViewCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: ViewType = ViewType.page
    filter: Optional[dict[str, Any]] = None
    sort: Optional[dict[str, Any]] = None


class ViewUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ViewType] = None
    filter: Optional[dict[str, Any]] = None
    sort: Optional[dict[str, Any]] = None
