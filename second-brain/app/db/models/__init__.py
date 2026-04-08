"""Import all models so SQLModel registers them for Alembic."""
from app.db.models.entry import Entry
from app.db.models.entry_block import EntryBlock
from app.db.models.relation import Relation
from app.db.models.view import View
from app.db.models.view_item import ViewItem
from app.db.models.update_log import UpdateLog

__all__ = ["Entry", "EntryBlock", "Relation", "View", "ViewItem", "UpdateLog"]
