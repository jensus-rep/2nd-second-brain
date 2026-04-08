"""Entry, Block, and Relation API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.api.deps import db_session
from app.schemas.common import ok, err
from app.schemas.entry import EntryCreate, EntryUpdate
from app.schemas.block import BlockCreate, BlockUpdate, BlockReorderRequest
from app.schemas.relation import RelationCreate
from app.services import entry_service, block_service, relation_service

router = APIRouter(prefix="/api/v1")


# ── Entries ───────────────────────────────────────────────────────────────────

@router.get("/entries")
def list_entries(
    status: Optional[str] = None,
    category: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(db_session),
) -> dict:
    entries = entry_service.list_entries(session, status=status, category=category, offset=offset, limit=limit)
    return ok([e.model_dump() for e in entries])


@router.post("/entries", status_code=201)
def create_entry(body: EntryCreate, session: Session = Depends(db_session)) -> dict:
    entry = entry_service.create_entry(session, body)
    return ok(entry.model_dump())


@router.get("/entries/{entry_id}")
def get_entry(entry_id: str, session: Session = Depends(db_session)) -> dict:
    entry = entry_service.get_entry(session, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Entry {entry_id!r} not found"))
    return ok(entry.model_dump())


@router.patch("/entries/{entry_id}")
def update_entry(entry_id: str, body: EntryUpdate, session: Session = Depends(db_session)) -> dict:
    entry = entry_service.update_entry(session, entry_id, body)
    if not entry:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Entry {entry_id!r} not found"))
    return ok(entry.model_dump())


@router.delete("/entries/{entry_id}", status_code=204)
def delete_entry(entry_id: str, session: Session = Depends(db_session)) -> None:
    deleted = entry_service.delete_entry(session, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Entry {entry_id!r} not found"))


# ── Blocks ────────────────────────────────────────────────────────────────────

@router.post("/entries/{entry_id}/blocks", status_code=201)
def append_block(entry_id: str, body: BlockCreate, session: Session = Depends(db_session)) -> dict:
    if not entry_service.get_entry_model(session, entry_id):
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Entry {entry_id!r} not found"))
    block = block_service.append_block(session, entry_id, body)
    return ok(block.model_dump())


@router.patch("/entries/{entry_id}/blocks/{block_id}")
def update_block(
    entry_id: str, block_id: str, body: BlockUpdate, session: Session = Depends(db_session)
) -> dict:
    block = block_service.update_block(session, entry_id, block_id, body)
    if not block:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Block {block_id!r} not found"))
    return ok(block.model_dump())


@router.delete("/entries/{entry_id}/blocks/{block_id}", status_code=204)
def delete_block(entry_id: str, block_id: str, session: Session = Depends(db_session)) -> None:
    deleted = block_service.delete_block(session, entry_id, block_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Block {block_id!r} not found"))


@router.post("/entries/{entry_id}/blocks/reorder")
def reorder_blocks(
    entry_id: str, body: BlockReorderRequest, session: Session = Depends(db_session)
) -> dict:
    if not entry_service.get_entry_model(session, entry_id):
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Entry {entry_id!r} not found"))
    try:
        blocks = block_service.reorder_blocks(session, entry_id, body.block_ids)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=err("INVALID_REORDER", str(exc)))
    return ok([b.model_dump() for b in blocks])


# ── Relations ─────────────────────────────────────────────────────────────────

@router.post("/entries/{entry_id}/relations", status_code=201)
def create_relation(
    entry_id: str, body: RelationCreate, session: Session = Depends(db_session)
) -> dict:
    relation, error = relation_service.create_relation(session, entry_id, body)
    if error:
        raise HTTPException(status_code=422, detail=err("INVALID_REFERENCE", error))
    return ok(relation.model_dump())


@router.delete("/entries/{entry_id}/relations/{relation_id}", status_code=204)
def delete_relation(entry_id: str, relation_id: str, session: Session = Depends(db_session)) -> None:
    deleted = relation_service.delete_relation(session, entry_id, relation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=err("NOT_FOUND", f"Relation {relation_id!r} not found"))
