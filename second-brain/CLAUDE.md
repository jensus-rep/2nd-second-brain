# CLAUDE.md — Second Brain Project

## Project Overview

Second Brain is a structured knowledge system built with:
- **FastAPI** backend
- **SQLModel + SQLAlchemy 2.x** ORM
- **SQLite** (local development)
- **Alembic** migrations
- **Jinja2** server-rendered templates
- **HTMX** for targeted interactivity
- No React, no SPA framework

## Running the Project

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Running Tests

```bash
pytest app/tests/ -v
```

## Key Architectural Rules

1. **IDs are server-generated** — always use `app/core/ids.py`. Never let clients or LLMs generate final IDs.
2. **UTC everywhere** — use `app.core.clock.utcnow()` for all timestamps.
3. **meta is always a dict** at the API boundary, never a raw JSON string. Persistence layer serializes to `meta_json` column.
4. **Snapshot ≠ Update Matrix** — these are different concepts. Don't mix them.
5. **Explicit positions** — every ordered collection uses an integer `position` field.
6. **No implicit deletions** — missing data in patches or snapshots never means delete.
7. **Thin routes** — routes call services, not the other way around.
8. **Reorder ops require complete sets** — `reorder_blocks` and `reorder_view_items` must include all IDs.

## File Structure

```
app/
├── core/ids.py          — Central ID generation (DO NOT bypass this)
├── core/clock.py        — UTC timestamps
├── core/enums.py        — All domain enumerations
├── core/json.py         — JSON serialization helpers
├── db/models/           — SQLModel ORM tables
├── schemas/             — Pydantic API contracts
│   ├── update_matrix.py — Discriminated union of all operations
│   └── snapshot.py      — Snapshot export/import shapes
├── services/            — Business logic
│   ├── update_matrix_service.py — Core mutation engine
│   └── snapshot_service.py     — Export/import
└── api/routes/          — FastAPI route handlers
```

## Adding New Operations to Update Matrix

1. Add new op model in `app/schemas/update_matrix.py`
2. Add to the `AnyOperation` union
3. Add handler function `_handle_<op_name>` in `update_matrix_service.py`
4. Register in `_HANDLERS` dict
5. Write tests in `app/tests/test_update_matrix.py`

## Adding New Block Types

1. Add to `BlockType` enum in `app/core/enums.py`
2. Add rendering in `app/services/render_service.py`
3. Update `_render_block()` switch

## Migrations

```bash
# After model changes:
alembic revision --autogenerate -m "brief description"
alembic upgrade head
```

## Database Notes

- SQLite with `check_same_thread=False` for development
- Cascade deletes: Entry → Blocks, Relations (both directions), ViewItems
- View → ViewItems
- All foreign keys use string IDs, not integers

## Response Format

All API responses use:
```json
{ "ok": true, "data": { ... } }
{ "ok": false, "error": { "code": "...", "message": "...", "details": null } }
```

Use `app.schemas.common.ok()` and `app.schemas.common.err()` helpers.
