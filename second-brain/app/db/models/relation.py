"""Relation DB model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.core.ids import relation_id
from app.core.clock import utcnow

if TYPE_CHECKING:
    from app.db.models.entry import Entry


class Relation(SQLModel, table=True):
    __tablename__ = "relations"

    id: str = Field(default_factory=relation_id, primary_key=True, max_length=20)
    source_entry_id: str = Field(foreign_key="entries.id", index=True, max_length=20)
    target_entry_id: str = Field(foreign_key="entries.id", index=True, max_length=20)
    relation_type: str = Field(max_length=50)
    position: int = Field(default=0)
    created_at: datetime = Field(default_factory=utcnow)

    source_entry: Optional["Entry"] = Relationship(
        back_populates="outgoing_relations",
        sa_relationship_kwargs={"foreign_keys": "[Relation.source_entry_id]"},
    )
    target_entry: Optional["Entry"] = Relationship(
        back_populates="incoming_relations",
        sa_relationship_kwargs={"foreign_keys": "[Relation.target_entry_id]"},
    )
