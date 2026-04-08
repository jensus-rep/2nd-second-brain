"""
Update Matrix engine.

Rules enforced:
- strict mode = all-or-nothing rollback on any failure
- best_effort = apply valid ops, log per-op failures
- temp_id references resolve within the same transaction
- no implicit deletions
- explicit typed operations only
- reference validation before commit
"""
import json
from typing import Any
from sqlmodel import Session, select
from app.core.clock import utcnow
from app.core import json as json_util
from app.core.enums import TransactionMode, UpdateStatus, SourceType
from app.db.models.entry import Entry
from app.db.models.entry_block import EntryBlock
from app.db.models.relation import Relation
from app.db.models.view import View
from app.db.models.view_item import ViewItem
from app.db.models.update_log import UpdateLog
from app.schemas.update_matrix import (
    UpdateMatrix, AnyOperation, UpdateMatrixResult, OperationResult,
    OpCreateEntry, OpUpdateEntry, OpDeleteEntry, OpArchiveEntry,
    OpAppendBlock, OpInsertBlock, OpUpdateBlock, OpDeleteBlock, OpReorderBlocks,
    OpLinkEntries, OpUnlinkRelation,
    OpCreateView, OpUpdateView, OpDeleteView,
    OpAddViewItem, OpRemoveViewItem, OpReorderViewItems,
)
from app.core.ids import entry_id as gen_entry_id, view_id as gen_view_id


class _ExecutionContext:
    """Mutable state threaded through one transaction."""

    def __init__(self) -> None:
        self.temp_id_map: dict[str, str] = {}
        self.created = 0
        self.updated = 0
        self.deleted = 0

    def resolve(self, ref: str) -> str:
        """Resolve a temp_id to its final ID, or return as-is if already final."""
        return self.temp_id_map.get(ref, ref)


# ── Per-operation handlers ────────────────────────────────────────────────────

def _handle_create_entry(op: OpCreateEntry, session: Session, ctx: _ExecutionContext) -> None:
    entry = Entry(
        title=op.data.title,
        slug=op.data.slug,
        category=op.data.category,
        status=op.data.status,
        summary=op.data.summary,
    )
    session.add(entry)
    session.flush()  # populate entry.id
    if op.temp_id:
        ctx.temp_id_map[op.temp_id] = entry.id
    ctx.created += 1


def _handle_update_entry(op: OpUpdateEntry, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_id)
    entry = session.get(Entry, entry_id)
    if not entry:
        raise LookupError(f"Entry {entry_id!r} not found")
    data = op.patch.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(entry, key, value)
    entry.updated_at = utcnow()
    session.add(entry)
    ctx.updated += 1


def _handle_delete_entry(op: OpDeleteEntry, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_id)
    entry = session.get(Entry, entry_id)
    if not entry:
        raise LookupError(f"Entry {entry_id!r} not found")
    session.delete(entry)
    ctx.deleted += 1


def _handle_archive_entry(op: OpArchiveEntry, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_id)
    entry = session.get(Entry, entry_id)
    if not entry:
        raise LookupError(f"Entry {entry_id!r} not found")
    entry.status = "archived"
    entry.updated_at = utcnow()
    session.add(entry)
    ctx.updated += 1


def _handle_append_block(op: OpAppendBlock, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_ref)
    entry = session.get(Entry, entry_id)
    if not entry:
        raise LookupError(f"Entry {entry_id!r} not found")
    meta = op.data.meta
    block = EntryBlock(
        entry_id=entry_id,
        type=op.data.type,
        content=op.data.content,
        position=op.data.position,
        meta_json=json_util.dumps(meta) if meta is not None else None,
    )
    session.add(block)
    ctx.created += 1


def _handle_insert_block(op: OpInsertBlock, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_ref)
    entry = session.get(Entry, entry_id)
    if not entry:
        raise LookupError(f"Entry {entry_id!r} not found")
    # Shift existing blocks at or after the insert position
    stmt = select(EntryBlock).where(
        EntryBlock.entry_id == entry_id,
        EntryBlock.position >= op.data.position,
    )
    for b in session.exec(stmt).all():
        b.position += 1
        session.add(b)
    meta = op.data.meta
    block = EntryBlock(
        entry_id=entry_id,
        type=op.data.type,
        content=op.data.content,
        position=op.data.position,
        meta_json=json_util.dumps(meta) if meta is not None else None,
    )
    session.add(block)
    ctx.created += 1


def _handle_update_block(op: OpUpdateBlock, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_id)
    stmt = select(EntryBlock).where(
        EntryBlock.id == op.block_id, EntryBlock.entry_id == entry_id
    )
    block = session.exec(stmt).first()
    if not block:
        raise LookupError(f"Block {op.block_id!r} in entry {entry_id!r} not found")
    data = op.patch.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "meta":
            block.meta_json = json_util.dumps(value) if value is not None else None
        else:
            setattr(block, key, value)
    block.updated_at = utcnow()
    session.add(block)
    ctx.updated += 1


def _handle_delete_block(op: OpDeleteBlock, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_id)
    stmt = select(EntryBlock).where(
        EntryBlock.id == op.block_id, EntryBlock.entry_id == entry_id
    )
    block = session.exec(stmt).first()
    if not block:
        raise LookupError(f"Block {op.block_id!r} not found")
    session.delete(block)
    ctx.deleted += 1


def _handle_reorder_blocks(op: OpReorderBlocks, session: Session, ctx: _ExecutionContext) -> None:
    entry_id = ctx.resolve(op.entry_id)
    stmt = select(EntryBlock).where(EntryBlock.entry_id == entry_id)
    existing = session.exec(stmt).all()
    existing_ids = {b.id for b in existing}
    incoming_ids = set(op.block_ids)
    if existing_ids != incoming_ids:
        raise ValueError(f"block_ids mismatch for entry {entry_id!r}")
    block_map = {b.id: b for b in existing}
    for position, bid in enumerate(op.block_ids):
        block_map[bid].position = position
        block_map[bid].updated_at = utcnow()
        session.add(block_map[bid])
    ctx.updated += len(op.block_ids)


def _handle_link_entries(op: OpLinkEntries, session: Session, ctx: _ExecutionContext) -> None:
    src_id = ctx.resolve(op.data.source_entry_id)
    tgt_id = ctx.resolve(op.data.target_entry_id)
    if not session.get(Entry, src_id):
        raise LookupError(f"Source entry {src_id!r} not found")
    if not session.get(Entry, tgt_id):
        raise LookupError(f"Target entry {tgt_id!r} not found")
    rel = Relation(
        source_entry_id=src_id,
        target_entry_id=tgt_id,
        relation_type=op.data.relation_type,
        position=op.data.position,
    )
    session.add(rel)
    ctx.created += 1


def _handle_unlink_relation(op: OpUnlinkRelation, session: Session, ctx: _ExecutionContext) -> None:
    rel = session.get(Relation, op.relation_id)
    if not rel:
        raise LookupError(f"Relation {op.relation_id!r} not found")
    session.delete(rel)
    ctx.deleted += 1


def _handle_create_view(op: OpCreateView, session: Session, ctx: _ExecutionContext) -> None:
    f = op.data.filter
    s = op.data.sort
    view = View(
        title=op.data.title,
        description=op.data.description,
        type=op.data.type,
        filter_json=json_util.dumps(f) if f is not None else None,
        sort_json=json_util.dumps(s) if s is not None else None,
    )
    session.add(view)
    session.flush()
    if op.temp_id:
        ctx.temp_id_map[op.temp_id] = view.id
    ctx.created += 1


def _handle_update_view(op: OpUpdateView, session: Session, ctx: _ExecutionContext) -> None:
    view_id = ctx.resolve(op.view_id)
    view = session.get(View, view_id)
    if not view:
        raise LookupError(f"View {view_id!r} not found")
    data = op.patch.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "filter":
            view.filter_json = json_util.dumps(value) if value is not None else None
        elif key == "sort":
            view.sort_json = json_util.dumps(value) if value is not None else None
        else:
            setattr(view, key, value)
    view.updated_at = utcnow()
    session.add(view)
    ctx.updated += 1


def _handle_delete_view(op: OpDeleteView, session: Session, ctx: _ExecutionContext) -> None:
    view_id = ctx.resolve(op.view_id)
    view = session.get(View, view_id)
    if not view:
        raise LookupError(f"View {view_id!r} not found")
    session.delete(view)
    ctx.deleted += 1


def _handle_add_view_item(op: OpAddViewItem, session: Session, ctx: _ExecutionContext) -> None:
    view_id = ctx.resolve(op.data.view_id)
    entry_id = ctx.resolve(op.data.entry_id)
    if not session.get(View, view_id):
        raise LookupError(f"View {view_id!r} not found")
    if not session.get(Entry, entry_id):
        raise LookupError(f"Entry {entry_id!r} not found")
    item = ViewItem(
        view_id=view_id,
        entry_id=entry_id,
        position=op.data.position,
        section_label=op.data.section_label,
    )
    session.add(item)
    ctx.created += 1


def _handle_remove_view_item(op: OpRemoveViewItem, session: Session, ctx: _ExecutionContext) -> None:
    item = session.get(ViewItem, op.view_item_id)
    if not item:
        raise LookupError(f"ViewItem {op.view_item_id!r} not found")
    session.delete(item)
    ctx.deleted += 1


def _handle_reorder_view_items(op: OpReorderViewItems, session: Session, ctx: _ExecutionContext) -> None:
    view_id = ctx.resolve(op.view_id)
    stmt = select(ViewItem).where(ViewItem.view_id == view_id)
    existing = session.exec(stmt).all()
    existing_ids = {i.id for i in existing}
    incoming_ids = set(op.item_ids)
    if existing_ids != incoming_ids:
        raise ValueError(f"item_ids mismatch for view {view_id!r}")
    item_map = {i.id: i for i in existing}
    for position, iid in enumerate(op.item_ids):
        item_map[iid].position = position
        session.add(item_map[iid])
    ctx.updated += len(op.item_ids)


# ── Dispatch table ────────────────────────────────────────────────────────────

_HANDLERS: dict[str, Any] = {
    "create_entry": _handle_create_entry,
    "update_entry": _handle_update_entry,
    "delete_entry": _handle_delete_entry,
    "archive_entry": _handle_archive_entry,
    "append_block": _handle_append_block,
    "insert_block": _handle_insert_block,
    "update_block": _handle_update_block,
    "delete_block": _handle_delete_block,
    "reorder_blocks": _handle_reorder_blocks,
    "link_entries": _handle_link_entries,
    "unlink_relation": _handle_unlink_relation,
    "create_view": _handle_create_view,
    "update_view": _handle_update_view,
    "delete_view": _handle_delete_view,
    "add_view_item": _handle_add_view_item,
    "remove_view_item": _handle_remove_view_item,
    "reorder_view_items": _handle_reorder_view_items,
}


# ── Main entry point ──────────────────────────────────────────────────────────

def apply_update_matrix(
    session: Session,
    matrix: UpdateMatrix,
    source_type: str = SourceType.manual.value,
) -> UpdateMatrixResult:
    ctx = _ExecutionContext()
    op_results: list[OperationResult] = []
    status = UpdateStatus.applied.value
    payload_json = matrix.model_dump_json()

    is_strict = matrix.mode == TransactionMode.strict

    for idx, operation in enumerate(matrix.operations):
        handler = _HANDLERS.get(operation.op)
        if not handler:
            op_results.append(OperationResult(index=idx, op=operation.op, status="rejected", error=f"Unknown op {operation.op!r}"))
            if is_strict:
                session.rollback()
                status = UpdateStatus.rejected.value
                break
            status = UpdateStatus.partial.value
            continue

        try:
            handler(operation, session, ctx)
            op_results.append(OperationResult(index=idx, op=operation.op, status="applied"))
        except (LookupError, ValueError) as exc:
            op_results.append(OperationResult(index=idx, op=operation.op, status="rejected", error=str(exc)))
            if is_strict:
                session.rollback()
                status = UpdateStatus.rejected.value
                # Clear accumulated state — rollback means nothing was persisted
                ctx.temp_id_map.clear()
                ctx.created = ctx.updated = ctx.deleted = 0
                # Mark remaining ops as skipped
                for rem_idx in range(idx + 1, len(matrix.operations)):
                    rem_op = matrix.operations[rem_idx]
                    op_results.append(OperationResult(index=rem_idx, op=rem_op.op, status="skipped"))
                break
            status = UpdateStatus.partial.value

    else:
        # All ops processed without breaking
        if status == UpdateStatus.applied.value:
            session.commit()
        # partial = already partial, still commit successful ops
        if status == UpdateStatus.partial.value:
            session.commit()

    result = UpdateMatrixResult(
        transaction_id=matrix.transaction_id,
        mode=matrix.mode.value,
        status=status,
        temp_id_map=ctx.temp_id_map,
        counts={"created": ctx.created, "updated": ctx.updated, "deleted": ctx.deleted},
        operations=op_results,
    )

    # Write UpdateLog regardless of outcome
    _write_log(session, source_type, payload_json, result)

    return result


def _write_log(
    session: Session,
    source_type: str,
    payload_json: str,
    result: UpdateMatrixResult,
) -> None:
    log = UpdateLog(
        source_type=source_type,
        payload_json=payload_json,
        result_json=result.model_dump_json(),
        status=result.status,
        created_entities=result.counts.get("created", 0),
        updated_entities=result.counts.get("updated", 0),
        deleted_entities=result.counts.get("deleted", 0),
    )
    session.add(log)
    try:
        session.commit()
    except Exception:
        pass  # Logging failure must not break response
