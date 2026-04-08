"""Block CRUD and reorder service."""
from typing import Optional
from sqlmodel import Session, select
from app.core.clock import utcnow
from app.core import json as json_util
from app.db.models.entry_block import EntryBlock
from app.schemas.block import BlockCreate, BlockRead, BlockUpdate


def _to_read(b: EntryBlock) -> BlockRead:
    return BlockRead(
        id=b.id,
        type=b.type,
        content=b.content,
        position=b.position,
        meta=json_util.loads(b.meta_json),
        created_at=b.created_at,
        updated_at=b.updated_at,
    )


def get_blocks_for_entry(session: Session, entry_id: str) -> list[BlockRead]:
    stmt = select(EntryBlock).where(EntryBlock.entry_id == entry_id).order_by(EntryBlock.position)
    return [_to_read(b) for b in session.exec(stmt).all()]


def get_block(session: Session, entry_id: str, block_id: str) -> Optional[EntryBlock]:
    stmt = select(EntryBlock).where(
        EntryBlock.id == block_id, EntryBlock.entry_id == entry_id
    )
    return session.exec(stmt).first()


def append_block(session: Session, entry_id: str, data: BlockCreate) -> BlockRead:
    block = EntryBlock(
        entry_id=entry_id,
        type=data.type.value if hasattr(data.type, "value") else data.type,
        content=data.content,
        position=data.position,
        meta_json=json_util.dumps(data.meta) if data.meta is not None else None,
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    return _to_read(block)


def insert_block(session: Session, entry_id: str, data: BlockCreate) -> BlockRead:
    """Insert a block at a specific position, shifting existing blocks."""
    stmt = select(EntryBlock).where(
        EntryBlock.entry_id == entry_id,
        EntryBlock.position >= data.position,
    )
    existing = session.exec(stmt).all()
    for b in existing:
        b.position += 1
        session.add(b)

    block = EntryBlock(
        entry_id=entry_id,
        type=data.type.value if hasattr(data.type, "value") else data.type,
        content=data.content,
        position=data.position,
        meta_json=json_util.dumps(data.meta) if data.meta is not None else None,
    )
    session.add(block)
    session.commit()
    session.refresh(block)
    return _to_read(block)


def update_block(
    session: Session, entry_id: str, block_id: str, patch: BlockUpdate
) -> Optional[BlockRead]:
    block = get_block(session, entry_id, block_id)
    if not block:
        return None
    data = patch.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "meta":
            block.meta_json = json_util.dumps(value) if value is not None else None
        elif key == "type" and hasattr(value, "value"):
            block.type = value.value
        else:
            setattr(block, key, value)
    block.updated_at = utcnow()
    session.add(block)
    session.commit()
    session.refresh(block)
    return _to_read(block)


def delete_block(session: Session, entry_id: str, block_id: str) -> bool:
    block = get_block(session, entry_id, block_id)
    if not block:
        return False
    session.delete(block)
    session.commit()
    return True


def reorder_blocks(session: Session, entry_id: str, block_ids: list[str]) -> list[BlockRead]:
    """
    Reorder blocks to match block_ids order.
    block_ids must be the complete set of block IDs for the entry.
    Raises ValueError if the IDs don't match the existing set.
    """
    stmt = select(EntryBlock).where(EntryBlock.entry_id == entry_id)
    existing = session.exec(stmt).all()
    existing_ids = {b.id for b in existing}
    incoming_ids = set(block_ids)

    if existing_ids != incoming_ids:
        missing = existing_ids - incoming_ids
        extra = incoming_ids - existing_ids
        raise ValueError(
            f"block_ids mismatch. Missing from request: {missing}. Unknown IDs: {extra}"
        )

    block_map = {b.id: b for b in existing}
    for position, bid in enumerate(block_ids):
        block_map[bid].position = position
        block_map[bid].updated_at = utcnow()
        session.add(block_map[bid])

    session.commit()
    return [_to_read(block_map[bid]) for bid in block_ids]
