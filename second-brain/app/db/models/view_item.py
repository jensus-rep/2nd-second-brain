"""ViewItem DB model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.core.ids import view_item_id
from app.core.clock import utcnow

if TYPE_CHECKING:
    from app.db.models.view import View
    from app.db.models.entry import Entry


class ViewItem(SQLModel, table=True):
    __tablename__ = "view_items"

    id: str = Field(default_factory=view_item_id, primary_key=True, max_length=20)
    view_id: str = Field(foreign_key="views.id", index=True, max_length=25)
    entry_id: str = Field(foreign_key="entries.id", index=True, max_length=20)
    position: int = Field(default=0)
    section_label: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utcnow)

    view: Optional["View"] = Relationship(back_populates="items")
    entry: Optional["Entry"] = Relationship(back_populates="view_items")
