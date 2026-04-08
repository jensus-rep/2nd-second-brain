"""Relation CRUD service."""
from typing import Optional
from sqlmodel import Session, select
from app.db.models.entry import Entry
from app.db.models.relation import Relation
from app.schemas.relation import RelationCreate, RelationRead


def _to_read(r: Relation) -> RelationRead:
    return RelationRead(
        id=r.id,
        target_entry_id=r.target_entry_id,
        relation_type=r.relation_type,
        position=r.position,
        created_at=r.created_at,
    )


def create_relation(
    session: Session, source_entry_id: str, data: RelationCreate
) -> tuple[Optional[RelationRead], Optional[str]]:
    """
    Returns (relation, error_message).
    Validates both source and target entries exist.
    """
    if not session.get(Entry, source_entry_id):
        return None, f"Source entry {source_entry_id!r} not found"
    if not session.get(Entry, data.target_entry_id):
        return None, f"Target entry {data.target_entry_id!r} not found"

    relation = Relation(
        source_entry_id=source_entry_id,
        target_entry_id=data.target_entry_id,
        relation_type=data.relation_type.value if hasattr(data.relation_type, "value") else data.relation_type,
        position=data.position,
    )
    session.add(relation)
    session.commit()
    session.refresh(relation)
    return _to_read(relation), None


def delete_relation(session: Session, entry_id: str, relation_id: str) -> bool:
    stmt = select(Relation).where(
        Relation.id == relation_id,
        Relation.source_entry_id == entry_id,
    )
    relation = session.exec(stmt).first()
    if not relation:
        return False
    session.delete(relation)
    session.commit()
    return True


def get_relation(session: Session, relation_id: str) -> Optional[Relation]:
    return session.get(Relation, relation_id)
