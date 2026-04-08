"""View DB model."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel
from app.core.ids import view_id
from app.core.clock import utcnow

if TYPE_CHECKING:
    from app.db.models.view_item import ViewItem


class View(SQLModel, table=True):
    __tablename__ = "views"

    id: str = Field(default_factory=view_id, primary_key=True, max_length=25)
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    type: str = Field(max_length=50)
    filter_json: Optional[str] = Field(default=None)
    sort_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    items: list["ViewItem"] = Relationship(
        back_populates="view",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "ViewItem.position"},
    )
