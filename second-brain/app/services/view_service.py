"""View and ViewItem CRUD service."""
from typing import Optional
from sqlmodel import Session, select
from app.core.clock import utcnow
from app.core import json as json_util
from app.db.models.entry import Entry
from app.db.models.view import View
from app.db.models.view_item import ViewItem
from app.schemas.view import (
    ViewCreate, ViewListItem, ViewRead, ViewUpdate,
    ViewItemCreate, ViewItemRead,
)


def _item_to_read(vi: ViewItem) -> ViewItemRead:
    return ViewItemRead(
        id=vi.id,
        entry_id=vi.entry_id,
        position=vi.position,
        section_label=vi.section_label,
        created_at=vi.created_at,
    )


def _view_to_read(v: View) -> ViewRead:
    items = sorted(v.items, key=lambda i: i.position)
    return ViewRead(
        id=v.id,
        title=v.title,
        description=v.description,
        type=v.type,
        filter=json_util.loads(v.filter_json),
        sort=json_util.loads(v.sort_json),
        items=[_item_to_read(i) for i in items],
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


def _view_to_list_item(v: View) -> ViewListItem:
    return ViewListItem(
        id=v.id,
        title=v.title,
        description=v.description,
        type=v.type,
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


def list_views(session: Session) -> list[ViewListItem]:
    stmt = select(View).order_by(View.updated_at.desc())
    return [_view_to_list_item(v) for v in session.exec(stmt).all()]


def get_view(session: Session, view_id: str) -> Optional[ViewRead]:
    v = session.get(View, view_id)
    return _view_to_read(v) if v else None


def get_view_model(session: Session, view_id: str) -> Optional[View]:
    return session.get(View, view_id)


def create_view(session: Session, data: ViewCreate) -> ViewRead:
    v = View(
        title=data.title,
        description=data.description,
        type=data.type.value if hasattr(data.type, "value") else data.type,
        filter_json=json_util.dumps(data.filter) if data.filter is not None else None,
        sort_json=json_util.dumps(data.sort) if data.sort is not None else None,
    )
    session.add(v)
    session.commit()
    session.refresh(v)
    return _view_to_read(v)


def update_view(session: Session, view_id: str, patch: ViewUpdate) -> Optional[ViewRead]:
    v = session.get(View, view_id)
    if not v:
        return None
    data = patch.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "filter":
            v.filter_json = json_util.dumps(value) if value is not None else None
        elif key == "sort":
            v.sort_json = json_util.dumps(value) if value is not None else None
        elif key == "type" and hasattr(value, "value"):
            v.type = value.value
        else:
            setattr(v, key, value)
    v.updated_at = utcnow()
    session.add(v)
    session.commit()
    session.refresh(v)
    return _view_to_read(v)


def delete_view(session: Session, view_id: str) -> bool:
    v = session.get(View, view_id)
    if not v:
        return False
    session.delete(v)
    session.commit()
    return True


def add_view_item(
    session: Session, view_id: str, data: ViewItemCreate
) -> tuple[Optional[ViewItemRead], Optional[str]]:
    if not session.get(View, view_id):
        return None, f"View {view_id!r} not found"
    if not session.get(Entry, data.entry_id):
        return None, f"Entry {data.entry_id!r} not found"

    item = ViewItem(
        view_id=view_id,
        entry_id=data.entry_id,
        position=data.position,
        section_label=data.section_label,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return _item_to_read(item), None


def remove_view_item(session: Session, view_id: str, view_item_id: str) -> bool:
    stmt = select(ViewItem).where(
        ViewItem.id == view_item_id, ViewItem.view_id == view_id
    )
    item = session.exec(stmt).first()
    if not item:
        return False
    session.delete(item)
    session.commit()
    return True


def reorder_view_items(
    session: Session, view_id: str, item_ids: list[str]
) -> tuple[list[ViewItemRead], Optional[str]]:
    stmt = select(ViewItem).where(ViewItem.view_id == view_id)
    existing = session.exec(stmt).all()
    existing_ids = {i.id for i in existing}
    incoming_ids = set(item_ids)

    if existing_ids != incoming_ids:
        missing = existing_ids - incoming_ids
        extra = incoming_ids - existing_ids
        return [], (
            f"item_ids mismatch. Missing from request: {missing}. Unknown IDs: {extra}"
        )

    item_map = {i.id: i for i in existing}
    for position, iid in enumerate(item_ids):
        item_map[iid].position = position
        session.add(item_map[iid])

    session.commit()
    return [_item_to_read(item_map[iid]) for iid in item_ids], None
