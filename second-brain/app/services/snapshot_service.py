"""
Snapshot service.
- Export: full state -> SnapshotExport
- Import: non-destructive upsert-by-id
"""
from datetime import datetime, timezone
from typing import Any
from sqlmodel import Session, select
from app.core.clock import utcnow
from app.core import json as json_util
from app.db.models.entry import Entry
from app.db.models.entry_block import EntryBlock
from app.db.models.relation import Relation
from app.db.models.view import View
from app.db.models.view_item import ViewItem
from app.schemas.snapshot import SnapshotExport, SnapshotImportResult
from app.schemas.entry import EntryRead
from app.schemas.block import BlockRead
from app.schemas.relation import RelationRead
from app.schemas.view import ViewRead, ViewItemRead


# ── Export ────────────────────────────────────────────────────────────────────

def export_snapshot(session: Session) -> SnapshotExport:
    entries = session.exec(select(Entry)).all()
    views = session.exec(select(View)).all()

    entry_reads: list[EntryRead] = []
    for entry in entries:
        blocks = sorted(entry.blocks, key=lambda b: b.position)
        relations = sorted(entry.outgoing_relations, key=lambda r: r.position)
        entry_reads.append(
            EntryRead(
                id=entry.id,
                title=entry.title,
                slug=entry.slug,
                category=entry.category,
                status=entry.status,
                summary=entry.summary,
                blocks=[
                    BlockRead(
                        id=b.id,
                        type=b.type,
                        content=b.content,
                        position=b.position,
                        meta=json_util.loads(b.meta_json),
                        created_at=b.created_at,
                        updated_at=b.updated_at,
                    )
                    for b in blocks
                ],
                relations=[
                    RelationRead(
                        id=r.id,
                        target_entry_id=r.target_entry_id,
                        relation_type=r.relation_type,
                        position=r.position,
                        created_at=r.created_at,
                    )
                    for r in relations
                ],
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
        )

    view_reads: list[ViewRead] = []
    for v in views:
        items = sorted(v.items, key=lambda i: i.position)
        view_reads.append(
            ViewRead(
                id=v.id,
                title=v.title,
                description=v.description,
                type=v.type,
                filter=json_util.loads(v.filter_json),
                sort=json_util.loads(v.sort_json),
                items=[
                    ViewItemRead(
                        id=i.id,
                        entry_id=i.entry_id,
                        position=i.position,
                        section_label=i.section_label,
                        created_at=i.created_at,
                    )
                    for i in items
                ],
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
        )

    return SnapshotExport(
        exported_at=utcnow(),
        entries=entry_reads,
        views=view_reads,
    )


def _parse_dt(value: Any, fallback: datetime) -> datetime:
    """Parse a datetime string or datetime object; return fallback if None."""
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return fallback
    return fallback


# ── Import ────────────────────────────────────────────────────────────────────

def import_snapshot(session: Session, snapshot: dict[str, Any]) -> SnapshotImportResult:
    """
    Non-destructive upsert-by-id.
    Missing entities in snapshot do NOT mean delete.
    """
    result = SnapshotImportResult(imported_at=utcnow())
    errors: list[str] = []

    # ── Import entries ────────────────────────────────────────────────────────
    for entry_data in snapshot.get("entries", []):
        entry_id = entry_data.get("id")
        if not entry_id:
            errors.append("Entry missing id, skipping")
            continue

        existing = session.get(Entry, entry_id)
        now = utcnow()

        if existing:
            existing.title = entry_data.get("title", existing.title)
            existing.slug = entry_data.get("slug", existing.slug)
            existing.category = entry_data.get("category", existing.category)
            existing.status = entry_data.get("status", existing.status)
            existing.summary = entry_data.get("summary", existing.summary)
            existing.updated_at = now
            session.add(existing)
            result.updated_entries += 1
        else:
            entry = Entry(
                id=entry_id,
                title=entry_data["title"],
                slug=entry_data.get("slug"),
                category=entry_data.get("category"),
                status=entry_data.get("status", "active"),
                summary=entry_data.get("summary"),
                created_at=_parse_dt(entry_data.get("created_at"), now),
                updated_at=_parse_dt(entry_data.get("updated_at"), now),
            )
            session.add(entry)
            result.created_entries += 1

        # Upsert blocks
        for block_data in entry_data.get("blocks", []):
            block_id = block_data.get("id")
            if not block_id:
                errors.append(f"Block in entry {entry_id!r} missing id, skipping")
                continue
            block_now = utcnow()
            existing_block = session.get(EntryBlock, block_id)
            meta = block_data.get("meta")
            meta_json = json_util.dumps(meta) if meta is not None else None
            if existing_block:
                existing_block.type = block_data.get("type", existing_block.type)
                existing_block.content = block_data.get("content", existing_block.content)
                existing_block.position = block_data.get("position", existing_block.position)
                existing_block.meta_json = meta_json if meta is not None else existing_block.meta_json
                existing_block.updated_at = block_now
                session.add(existing_block)
            else:
                block = EntryBlock(
                    id=block_id,
                    entry_id=entry_id,
                    type=block_data["type"],
                    content=block_data.get("content", ""),
                    position=block_data.get("position", 0),
                    meta_json=meta_json,
                    created_at=_parse_dt(block_data.get("created_at"), block_now),
                    updated_at=_parse_dt(block_data.get("updated_at"), block_now),
                )
                session.add(block)

        # Upsert outgoing relations
        for rel_data in entry_data.get("relations", []):
            rel_id = rel_data.get("id")
            if not rel_id:
                errors.append(f"Relation in entry {entry_id!r} missing id, skipping")
                continue
            if not session.get(Relation, rel_id):
                rel = Relation(
                    id=rel_id,
                    source_entry_id=entry_id,
                    target_entry_id=rel_data["target_entry_id"],
                    relation_type=rel_data["relation_type"],
                    position=rel_data.get("position", 0),
                    created_at=_parse_dt(rel_data.get("created_at"), utcnow()),
                )
                session.add(rel)

    # Flush entries before views (view_items FK to entries)
    session.flush()

    # ── Import views ──────────────────────────────────────────────────────────
    for view_data in snapshot.get("views", []):
        view_id = view_data.get("id")
        if not view_id:
            errors.append("View missing id, skipping")
            continue

        now = utcnow()
        f = view_data.get("filter")
        s = view_data.get("sort")
        existing_view = session.get(View, view_id)

        if existing_view:
            existing_view.title = view_data.get("title", existing_view.title)
            existing_view.description = view_data.get("description", existing_view.description)
            existing_view.type = view_data.get("type", existing_view.type)
            existing_view.filter_json = json_util.dumps(f) if f is not None else existing_view.filter_json
            existing_view.sort_json = json_util.dumps(s) if s is not None else existing_view.sort_json
            existing_view.updated_at = now
            session.add(existing_view)
            result.updated_views += 1
        else:
            view = View(
                id=view_id,
                title=view_data["title"],
                description=view_data.get("description"),
                type=view_data.get("type", "page"),
                filter_json=json_util.dumps(f) if f is not None else None,
                sort_json=json_util.dumps(s) if s is not None else None,
                created_at=_parse_dt(view_data.get("created_at"), now),
                updated_at=_parse_dt(view_data.get("updated_at"), now),
            )
            session.add(view)
            result.created_views += 1

        for item_data in view_data.get("items", []):
            item_id = item_data.get("id")
            if not item_id:
                errors.append(f"ViewItem in view {view_id!r} missing id, skipping")
                continue
            if not session.get(ViewItem, item_id):
                vi = ViewItem(
                    id=item_id,
                    view_id=view_id,
                    entry_id=item_data["entry_id"],
                    position=item_data.get("position", 0),
                    section_label=item_data.get("section_label"),
                    created_at=_parse_dt(item_data.get("created_at"), utcnow()),
                )
                session.add(vi)

    session.commit()
    result.errors = errors
    return result
