"""Entry CRUD service."""
from typing import Optional
from sqlmodel import Session, select
from app.core.clock import utcnow
from app.core.enums import EntryStatus
from app.core import json as json_util
from app.db.models.entry import Entry
from app.db.models.entry_block import EntryBlock
from app.db.models.relation import Relation
from app.schemas.entry import EntryCreate, EntryRead, EntryListItem, EntryUpdate
from app.schemas.block import BlockRead
from app.schemas.relation import RelationRead


def _block_to_read(b: EntryBlock) -> BlockRead:
    return BlockRead(
        id=b.id,
        type=b.type,
        content=b.content,
        position=b.position,
        meta=json_util.loads(b.meta_json),
        created_at=b.created_at,
        updated_at=b.updated_at,
    )


def _relation_to_read(r: Relation) -> RelationRead:
    return RelationRead(
        id=r.id,
        target_entry_id=r.target_entry_id,
        relation_type=r.relation_type,
        position=r.position,
        created_at=r.created_at,
    )


def _entry_to_read(entry: Entry) -> EntryRead:
    blocks = sorted(entry.blocks, key=lambda b: b.position)
    relations = sorted(entry.outgoing_relations, key=lambda r: r.position)
    return EntryRead(
        id=entry.id,
        title=entry.title,
        slug=entry.slug,
        category=entry.category,
        status=entry.status,
        summary=entry.summary,
        blocks=[_block_to_read(b) for b in blocks],
        relations=[_relation_to_read(r) for r in relations],
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _entry_to_list_item(entry: Entry) -> EntryListItem:
    return EntryListItem(
        id=entry.id,
        title=entry.title,
        slug=entry.slug,
        category=entry.category,
        status=entry.status,
        summary=entry.summary,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def list_entries(
    session: Session,
    status: Optional[str] = None,
    category: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> list[EntryListItem]:
    stmt = select(Entry)
    if status:
        stmt = stmt.where(Entry.status == status)
    if category:
        stmt = stmt.where(Entry.category == category)
    stmt = stmt.order_by(Entry.updated_at.desc()).offset(offset).limit(limit)
    return [_entry_to_list_item(e) for e in session.exec(stmt).all()]


def get_entry(session: Session, entry_id: str) -> Optional[EntryRead]:
    entry = session.get(Entry, entry_id)
    if not entry:
        return None
    return _entry_to_read(entry)


def get_entry_model(session: Session, entry_id: str) -> Optional[Entry]:
    return session.get(Entry, entry_id)


def create_entry(session: Session, data: EntryCreate) -> EntryRead:
    entry = Entry(
        title=data.title,
        slug=data.slug,
        category=data.category,
        status=data.status.value if hasattr(data.status, "value") else data.status,
        summary=data.summary,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _entry_to_read(entry)


def update_entry(session: Session, entry_id: str, patch: EntryUpdate) -> Optional[EntryRead]:
    entry = session.get(Entry, entry_id)
    if not entry:
        return None
    data = patch.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "status" and hasattr(value, "value"):
            value = value.value
        setattr(entry, key, value)
    entry.updated_at = utcnow()
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _entry_to_read(entry)


def delete_entry(session: Session, entry_id: str) -> bool:
    entry = session.get(Entry, entry_id)
    if not entry:
        return False
    session.delete(entry)
    session.commit()
    return True


def archive_entry(session: Session, entry_id: str) -> Optional[EntryRead]:
    entry = session.get(Entry, entry_id)
    if not entry:
        return None
    entry.status = EntryStatus.archived.value
    entry.updated_at = utcnow()
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _entry_to_read(entry)
