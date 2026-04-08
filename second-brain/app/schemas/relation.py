"""Relation schemas."""
from datetime import datetime
from pydantic import BaseModel
from app.core.enums import RelationType


class RelationRead(BaseModel):
    id: str
    target_entry_id: str
    relation_type: str
    position: int
    created_at: datetime


class RelationCreate(BaseModel):
    target_entry_id: str
    relation_type: RelationType
    position: int = 0
