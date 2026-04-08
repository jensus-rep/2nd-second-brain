# Second Brain — Rebuild Checklist

## Current Status
**COMPLETE** — All 5 phases done. 47/47 tests passing. Migration applied. App starts cleanly.

---

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend framework | FastAPI | Async, typed, production-ready |
| ORM | SQLModel + SQLAlchemy 2.x | Pydantic-native models |
| Database | SQLite (local) | Zero-config, portable |
| Migrations | Alembic | Industry standard, deterministic |
| Templates | Jinja2 | Server-rendered, no JS overhead |
| Interactivity | HTMX + minimal Alpine.js | Targeted DOM updates without React |
| ID generation | Custom prefix + 12-char alphanum | URL-safe, type-identifiable, server-side only |
| Timestamps | UTC everywhere | Unambiguous, portable |
| Mutation format | Update Matrix (typed operations) | Explicit, traceable, agent-friendly |
| State format | Snapshot (full export/import) | Round-trip capable, non-destructive |

---

## Phase 1 — Foundation ✅

- [x] Project skeleton created (`second-brain/`)
- [x] `app/core/ids.py` — central ID generation with type prefixes
- [x] `app/core/clock.py` — UTC clock utility
- [x] `app/core/enums.py` — all domain enumerations
- [x] `app/core/json.py` — JSON serialization helpers
- [x] `app/config.py` — settings with pydantic-settings
- [x] `app/db/base.py` — SQLModel metadata base
- [x] `app/db/session.py` — session factory
- [x] `app/db/models/entry.py` — Entry model
- [x] `app/db/models/entry_block.py` — EntryBlock model
- [x] `app/db/models/relation.py` — Relation model
- [x] `app/db/models/view.py` — View model
- [x] `app/db/models/view_item.py` — ViewItem model
- [x] `app/db/models/update_log.py` — UpdateLog model
- [x] `app/schemas/common.py` — response envelope
- [x] `app/schemas/entry.py` — Entry schemas
- [x] `app/schemas/block.py` — Block schemas
- [x] `app/schemas/relation.py` — Relation schemas
- [x] `app/schemas/view.py` — View and ViewItem schemas
- [x] `app/schemas/snapshot.py` — Snapshot export/import schemas
- [x] `app/schemas/update_matrix.py` — Update Matrix discriminated union schemas
- [x] `app/schemas/responses.py` — HealthResponse
- [x] `alembic.ini` — Alembic configuration
- [x] `alembic/env.py` — Migration environment
- [x] `alembic/versions/0001_initial_schema.py` — Initial migration
- [x] `requirements.txt`

---

## Phase 2 — CRUD Services and API Routes ✅

- [x] `app/services/entry_service.py`
- [x] `app/services/block_service.py`
- [x] `app/services/relation_service.py`
- [x] `app/services/view_service.py`
- [x] `app/api/deps.py`
- [x] `app/api/routes/health.py`
- [x] `app/api/routes/entries.py`
- [x] `app/api/routes/views.py`
- [x] `app/main.py`

---

## Phase 3 — Snapshot + Update Matrix Engine ✅

- [x] `app/services/snapshot_service.py`
- [x] `app/services/update_matrix_service.py`
- [x] `app/services/render_service.py`
- [x] `app/api/routes/import_export.py`
- [x] `app/db/models/update_log.py` — wired into Update Matrix service

---

## Phase 4 — UI ✅

- [x] `app/templates/layout.html`
- [x] `app/templates/home.html`
- [x] `app/templates/entries/list.html`
- [x] `app/templates/entries/detail.html`
- [x] `app/templates/entries/form.html`
- [x] `app/templates/entries/_blocks.html`
- [x] `app/templates/views/list.html`
- [x] `app/templates/views/detail.html`
- [x] `app/templates/views/_items.html`
- [x] `app/templates/imports/index.html`
- [x] `app/templates/exports/index.html`
- [x] `app/api/routes/ui.py`
- [x] `app/static/css/app.css`
- [x] `app/static/js/app.js`

---

## Phase 5 — Tests and Docs ✅

- [x] `app/tests/test_ids.py`
- [x] `app/tests/test_entries.py`
- [x] `app/tests/test_update_matrix.py`
- [x] `app/tests/test_snapshot_roundtrip.py`
- [x] `app/tests/test_views.py`
- [x] `docs/architecture.md`
- [x] `docs/json-contracts.md`
- [x] `docs/update-engine.md`
- [x] `README.md`
- [x] `CLAUDE.md`

**Test result: 47/47 passing**

---

## Phase 6 — Frontend Design System ✅

**Date completed:** 2026-04-09

### Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Typography | Inter (Google Fonts) | Readable, neutral, editorial quality |
| Base font size | 16px (up from 14px) | More comfortable reading size |
| Palette | Warm off-white bg, indigo accent | Knowledge-workspace feel, less "admin" |
| Block controls | Opacity 0 → 1 on hover | Content-first; controls available without clutter |
| Entry list | Row layout (not grid) | Easier scanning of titles and metadata |
| Entry detail | Hero + two-column | Title dominant, metadata in sidebar |
| Empty states | Illustrated with icon + copy | Friendly, not blank/broken |
| Filter bar | Styled surface, not raw inline | Visually secondary without being hidden |
| View items | Positioned list rows | Ordered reading flow is clear |

### Files changed

- [x] `app/static/css/app.css` — Full design system rewrite (~400 lines). Warm palette, Inter, generous spacing, new component library
- [x] `app/templates/layout.html` — Refined nav with brand mark, active underline indicator, clean aux links
- [x] `app/templates/home.html` — Welcoming headline, entry/view list rows, minimal quick-actions strip
- [x] `app/templates/entries/list.html` — Row-based list, styled filter bar, improved empty state
- [x] `app/templates/entries/detail.html` — Hero section (big title, summary as intro), sidebar metadata, disclosure for add-block and add-relation
- [x] `app/templates/entries/_blocks.html` — Block controls fade in on hover; per-type content classes; empty state
- [x] `app/templates/entries/form.html` — Clean form with label hints, logical field order
- [x] `app/templates/views/list.html` — Editorial card grid, description visible, improved empty state
- [x] `app/templates/views/detail.html` — Hero section, sidebar metadata, disclosure for add-item
- [x] `app/templates/views/_items.html` — Positioned row style, section labels, empty state
- [x] `app/templates/imports/index.html` — Cleaner two-panel layout, improved ops reference table
- [x] `app/templates/exports/index.html` — Stats header row, copy + download side-by-side

---

## Open Issues

- None currently

---

## Validation Notes

- IDs are prefix + 12 alphanumeric chars, URL-safe
- All timestamps use UTC
- API boundary: meta is always structured dict, never raw JSON string
- Snapshot import is non-destructive (upsert-by-id only)
- Update Matrix is transactional; strict mode = all-or-nothing
- temp_id resolution: later ops in same matrix can reference temp_ids from earlier ops
- Deletion of Entry cascades to Blocks, Relations (both directions), ViewItems
