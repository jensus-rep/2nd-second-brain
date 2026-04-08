"""EntryBlock DB model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.core.ids import block_id
from app.core.clock import utcnow

if TYPE_CHECKING:
    from app.db.models.entry import Entry


class EntryBlock(SQLModel, table=True):
    __tablename__ = "entry_blocks"

    id: str = Field(default_factory=block_id, primary_key=True, max_length=20)
    entry_id: str = Field(foreign_key="entries.id", index=True, max_length=20)
    type: str = Field(max_length=50)
    content: str = Field(default="")
    position: int = Field(default=0)
    meta_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    entry: Optional["Entry"] = Relationship(back_populates="blocks")
