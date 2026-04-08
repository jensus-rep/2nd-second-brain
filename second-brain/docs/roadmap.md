# Roadmap

## V1 (Current)

All items implemented and tested.

- Entry CRUD with ordered blocks
- Block types: text, markdown, code, list, table, quote
- Relation types: related, extends, contradicts, references, duplicate_of
- View and ViewItem management
- Snapshot export/import (round-trip, non-destructive)
- Update Matrix engine (strict and best_effort modes)
- temp_id resolution within transactions
- UpdateLog audit trail
- Server-rendered UI (Jinja2 + HTMX)
- Alembic migrations

## V2 Candidates (Not in scope for V1)

These are potential next additions. None are pre-built speculatively.

- **Full-text search** — SQLite FTS5 index on Entry titles and block content
- **Tag system** — lightweight many-to-many tags on entries
- **Block-level diffs** — visual diff between block versions
- **Entry versioning** — append-only change log per entry
- **Auth** — simple token-based auth for multi-user scenarios
- **Webhook / event push** — notify external systems on mutations
- **Embeddings** — vector similarity search via SQLite VSS extension
- **Agent API key** — dedicated scoped keys for LLM agents

## Non-Goals (Permanent)

- React or any SPA frontend
- Real-time collaboration (operational transforms, CRDTs)
- Complex role-based access control
- Heavy rich-text editors (Quill, TipTap, etc.)
- Productized multi-agent orchestration
- Full event sourcing architecture
