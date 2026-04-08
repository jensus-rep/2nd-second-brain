"""Block schemas — API boundary uses structured meta objects, never raw JSON strings."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, field_validator
from app.core.enums import BlockType


class BlockMeta(BaseModel):
    """Freeform structured metadata for list and table blocks."""
    model_config = {"extra": "allow"}


class BlockRead(BaseModel):
    id: str
    type: str
    content: str
    position: int
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class BlockCreate(BaseModel):
    type: BlockType
    content: str = ""
    position: int
    meta: Optional[dict[str, Any]] = None

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v: Any) -> BlockType:
        return BlockType(v)


class BlockUpdate(BaseModel):
    type: Optional[BlockType] = None
    content: Optional[str] = None
    position: Optional[int] = None
    meta: Optional[dict[str, Any]] = None


class BlockReorderRequest(BaseModel):
    """block_ids must be the complete ordered list of all block IDs for the entry."""
    block_ids: list[str]
