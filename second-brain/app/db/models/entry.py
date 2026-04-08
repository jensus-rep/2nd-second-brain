"""Entry DB model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.core.ids import entry_id
from app.core.clock import utcnow
from app.core.enums import EntryStatus

if TYPE_CHECKING:
    from app.db.models.entry_block import EntryBlock
    from app.db.models.relation import Relation
    from app.db.models.view_item import ViewItem


class Entry(SQLModel, table=True):
    __tablename__ = "entries"

    id: str = Field(default_factory=entry_id, primary_key=True, max_length=20)
    title: str = Field(max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255, index=True)
    category: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default=EntryStatus.active.value, max_length=20)
    summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    blocks: list["EntryBlock"] = Relationship(
        back_populates="entry",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "EntryBlock.position"},
    )
    outgoing_relations: list["Relation"] = Relationship(
        back_populates="source_entry",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": "[Relation.source_entry_id]",
        },
    )
    incoming_relations: list["Relation"] = Relationship(
        back_populates="target_entry",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": "[Relation.target_entry_id]",
        },
    )
    view_items: list["ViewItem"] = Relationship(
        back_populates="entry",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
