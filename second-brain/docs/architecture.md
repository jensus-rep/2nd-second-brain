# Second Brain — Architecture

## Overview

Three-layer architecture:

```
┌─────────────────────────────────────────────────┐
│  View Layer  (Jinja2 + HTMX + minimal Alpine.js) │
│  UI routes, templates, render_service            │
├─────────────────────────────────────────────────┤
│  Update Engine  (update_matrix_service)          │
│  Typed operations, strict/best_effort modes      │
│  temp_id resolution, UpdateLog                   │
├─────────────────────────────────────────────────┤
│  Content Store  (SQLite via SQLModel/SQLAlchemy) │
│  Entry, EntryBlock, Relation, View, ViewItem     │
│  Alembic migrations, UTC timestamps              │
└─────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Content Store
- Source of truth for all structured knowledge
- Persistent, addressable by stable server-generated IDs
- Ordered through explicit `position` fields
- Entries own Blocks; Views reference Entries without copying them

### Update Engine
- All mutations go through typed operation schemas
- Supports two transaction modes: `strict` (all-or-nothing) and `best_effort`
- Resolves `temp_id` references within a transaction
- Logs every transaction to `UpdateLog` regardless of outcome
- No implicit deletions; deletion must be an explicit operation

### View Layer
- Server-rendered HTML via Jinja2 templates
- Targeted DOM updates via HTMX (no full page reloads for common actions)
- Alpine.js used only where truly needed (none in V1)
- No React; no SPA framework; no client-side routing

## Key Design Decisions

| Decision | Rationale |
|---|---|
| SQLite | Zero-config, portable, sufficient for single-user knowledge system |
| SQLModel | Pydantic-native models eliminate impedance mismatch at API boundary |
| IDs: prefix + 12 alphanum | URL-safe, type-identifiable, human-readable in logs |
| UTC everywhere | Unambiguous timestamps, no timezone confusion |
| meta as structured dict | Clean API boundary; no JSON-inside-JSON strings |
| Snapshot ≠ Update Matrix | State (snapshot) and mutation (matrix) are fundamentally different concepts |
| position-based ordering | Deterministic, explicit; never rely on insertion order |

## Data Flow

### API Mutation
```
HTTP Request → Pydantic schema validation → Service function
→ DB Session → SQLModel ORM → SQLite
→ Pydantic response → JSON response envelope
```

### Update Matrix
```
POST /api/v1/import/update-matrix
→ UpdateMatrix schema (discriminated union)
→ update_matrix_service.apply_update_matrix()
  → _ExecutionContext (temp_id_map, counters)
  → per-op handlers (dispatched by op string)
  → session.flush() after each flush-needed op
  → session.commit() on success
  → session.rollback() on strict-mode failure
→ UpdateLog written
→ UpdateMatrixResult response
```

### Snapshot Round-Trip
```
Export: GET /api/v1/export/snapshot
→ snapshot_service.export_snapshot()
→ SnapshotExport (entries with blocks+relations, views with items)

Import: POST /api/v1/import/snapshot
→ snapshot_service.import_snapshot()
→ upsert-by-id for entries, blocks, relations, views, view_items
→ No deletions, no destructive replacement
→ SnapshotImportResult
```

## File Structure

```
app/
├── core/           — IDs, clock, enums, JSON utils
├── db/
│   ├── models/     — SQLModel ORM tables
│   └── session.py  — SQLAlchemy engine + session factory
├── schemas/        — Pydantic request/response/contract models
├── services/       — Business logic (no HTTP concerns)
├── api/
│   ├── deps.py     — FastAPI dependency injection
│   └── routes/     — Thin route handlers
└── templates/      — Jinja2 HTML templates
```

## ID Prefixes

| Prefix | Entity |
|---|---|
| `ent_` | Entry |
| `blk_` | EntryBlock |
| `rel_` | Relation |
| `view_` | View |
| `vi_` | ViewItem |
| `ulog_` | UpdateLog |

All IDs: `prefix + 12 alphanumeric characters`. Generated server-side only.
