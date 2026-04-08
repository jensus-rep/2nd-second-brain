# Second Brain

Structured knowledge system — FastAPI + SQLite + Jinja2 + HTMX.

No React. No SPA. No heavyweight platform complexity.

---

## Quickstart

```bash
cd second-brain

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
alembic upgrade head

# Run the server
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Architecture

Three layers:

1. **Content Store** — SQLite via SQLModel/SQLAlchemy. Entries, Blocks, Relations, Views.
2. **Update Engine** — Typed transactional mutations via Update Matrix.
3. **View Layer** — Server-rendered Jinja2 + HTMX.

See [docs/architecture.md](docs/architecture.md) for full details.

---

## Data Model

| Entity | ID Prefix | Description |
|---|---|---|
| Entry | `ent_` | A knowledge item with ordered blocks |
| EntryBlock | `blk_` | Content block within an Entry |
| Relation | `rel_` | Typed link between two Entries |
| View | `view_` | Curated collection of Entries |
| ViewItem | `vi_` | Entry reference within a View |
| UpdateLog | `ulog_` | Audit log of all Update Matrix transactions |

Block types: `text`, `markdown`, `code`, `list`, `table`, `quote`

Relation types: `related`, `extends`, `contradicts`, `references`, `duplicate_of`

---

## API Routes

### Health
- `GET /health`

### Entries
- `GET /api/v1/entries` — list (filter by `status`, `category`)
- `POST /api/v1/entries` — create
- `GET /api/v1/entries/{id}` — get with blocks and relations
- `PATCH /api/v1/entries/{id}` — partial update
- `DELETE /api/v1/entries/{id}` — delete (cascades blocks, relations, view items)

### Blocks
- `POST /api/v1/entries/{id}/blocks` — append block
- `PATCH /api/v1/entries/{id}/blocks/{block_id}` — update block
- `DELETE /api/v1/entries/{id}/blocks/{block_id}` — delete block
- `POST /api/v1/entries/{id}/blocks/reorder` — reorder (complete set required)

### Relations
- `POST /api/v1/entries/{id}/relations` — link entries
- `DELETE /api/v1/entries/{id}/relations/{relation_id}` — unlink

### Views
- `GET /api/v1/views`
- `POST /api/v1/views`
- `GET /api/v1/views/{id}`
- `PATCH /api/v1/views/{id}`
- `DELETE /api/v1/views/{id}`
- `POST /api/v1/views/{id}/items`
- `DELETE /api/v1/views/{id}/items/{item_id}`
- `POST /api/v1/views/{id}/items/reorder`

### Import / Export
- `GET /api/v1/export/snapshot` — export full state
- `POST /api/v1/import/snapshot` — non-destructive upsert import
- `POST /api/v1/import/update-matrix` — apply typed mutation transaction

---

## Update Matrix

The agent-facing mutation format. Supports `strict` (all-or-nothing) and `best_effort` modes.

```json
{
  "schema_version": "1.0",
  "mode": "strict",
  "operations": [
    {
      "op": "create_entry",
      "temp_id": "tmp_1",
      "data": { "title": "Prompt Chaining", "status": "active" }
    },
    {
      "op": "append_block",
      "entry_ref": "tmp_1",
      "data": { "type": "markdown", "content": "# Overview", "position": 0 }
    }
  ]
}
```

See [docs/json-contracts.md](docs/json-contracts.md) for full contract reference.

---

## Tests

```bash
pytest app/tests/ -v
```

---

## Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration (after model changes)
alembic revision --autogenerate -m "description"

# Rollback
alembic downgrade -1
```

---

## Configuration

Copy `.env.example` to `.env` and edit:

```
DATABASE_URL=sqlite:///./second_brain.db
DEBUG=false
DB_ECHO=false
```

---

## Design Principles

- **Server-generated IDs only** — clients never generate final IDs
- **UTC timestamps everywhere** — no timezone ambiguity
- **Explicit positions** — ordering is always deterministic
- **No implicit deletions** — missing data never means delete
- **State ≠ Mutation** — Snapshot and Update Matrix are different concepts
- **Thin routes** — no business logic in route handlers
- **No magic side effects** — mutations only touch what is explicitly targeted
