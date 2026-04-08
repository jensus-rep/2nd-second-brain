# JSON Contracts

## Two Distinct Concepts

**State ≠ Mutation**

| Concept | Format | Purpose |
|---|---|---|
| Snapshot | `SnapshotExport` | Full state: export, backup, round-trip import |
| Update Matrix | `UpdateMatrix` | Explicit mutations: agentic updates, transactions |

Do not conflate these. A snapshot is a photo; a matrix is a surgical plan.

---

## Canonical Entry Shape (API boundary)

```json
{
  "schema_version": "1.0",
  "id": "ent_xKq3mT9Rp1Lw",
  "title": "Prompt Engineering",
  "slug": "prompt-engineering",
  "category": "AI",
  "status": "active",
  "summary": "Methods for precise LLM output control",
  "blocks": [
    {
      "id": "blk_A1b2C3d4E5f6",
      "type": "markdown",
      "content": "## Core Idea\nPrompts control behavior...",
      "position": 0,
      "meta": null
    },
    {
      "id": "blk_G7h8I9j0K1l2",
      "type": "list",
      "content": "",
      "position": 1,
      "meta": {
        "items": ["Define role", "Define format", "Define constraints"]
      }
    }
  ],
  "relations": [
    {
      "id": "rel_AbCdEfGh1234",
      "target_entry_id": "ent_Z9y8X7w6V5u4",
      "relation_type": "related",
      "position": 0
    }
  ]
}
```

**Rules:**
- `meta` is always a structured object or `null` — never a JSON string
- `blocks` are always ordered by `position`
- `relations` are always outgoing (source = this entry)

---

## Canonical View Shape

```json
{
  "schema_version": "1.0",
  "id": "view_mN7pQ2rS8tUv",
  "title": "AI Overview",
  "description": "Curated knowledge map for AI",
  "type": "page",
  "filter": null,
  "sort": { "by": "title", "direction": "asc" },
  "items": [
    {
      "id": "vi_123abcXYZ789",
      "entry_id": "ent_xKq3mT9Rp1Lw",
      "position": 0,
      "section_label": "Fundamentals"
    }
  ]
}
```

---

## Snapshot Format

```json
{
  "schema_version": "1.0",
  "exported_at": "2026-04-08T10:30:00Z",
  "entries": [ /* EntryRead objects */ ],
  "views":   [ /* ViewRead objects */ ]
}
```

**Import rules:**
- Upsert-by-id: present IDs are created or updated
- Missing IDs are NOT deleted
- Import is safe to run multiple times (idempotent for same IDs)

---

## Update Matrix Format

```json
{
  "schema_version": "1.0",
  "transaction_id": "txn_20260408_001",
  "mode": "strict",
  "operations": [...]
}
```

### Transaction Modes

| Mode | Behavior |
|---|---|
| `strict` | All-or-nothing. Any failure rolls back all ops. |
| `best_effort` | Apply valid ops, report per-op failures. |

### temp_id Resolution

Operations may use `temp_id` to reference entities created earlier in the same transaction:

```json
{ "op": "create_entry", "temp_id": "tmp_e1", "data": { "title": "New" } },
{ "op": "append_block", "entry_ref": "tmp_e1", "data": { ... } }
```

The `temp_id_map` in the response resolves all temp IDs to final server IDs.

### All Operations

| op | Required fields |
|---|---|
| `create_entry` | `data.title`, `data.status` |
| `update_entry` | `entry_id`, `patch` |
| `delete_entry` | `entry_id` |
| `archive_entry` | `entry_id` |
| `append_block` | `entry_ref`, `data.type`, `data.position` |
| `insert_block` | `entry_ref`, `data.type`, `data.position` |
| `update_block` | `entry_id`, `block_id`, `patch` |
| `delete_block` | `entry_id`, `block_id` |
| `reorder_blocks` | `entry_id`, `block_ids` (complete set) |
| `link_entries` | `data.source_entry_id`, `data.target_entry_id`, `data.relation_type` |
| `unlink_relation` | `relation_id` |
| `create_view` | `data.title`, `data.type` |
| `update_view` | `view_id`, `patch` |
| `delete_view` | `view_id` |
| `add_view_item` | `data.view_id`, `data.entry_id` |
| `remove_view_item` | `view_item_id` |
| `reorder_view_items` | `view_id`, `item_ids` (complete set) |

### Update Matrix Result

```json
{
  "ok": true,
  "data": {
    "transaction_id": "txn_20260408_001",
    "mode": "strict",
    "status": "applied",
    "temp_id_map": { "tmp_e1": "ent_xKq3mT9Rp1Lw" },
    "counts": { "created": 2, "updated": 1, "deleted": 0 },
    "operations": [
      { "index": 0, "op": "create_entry", "status": "applied" },
      { "index": 1, "op": "append_block", "status": "applied" }
    ]
  }
}
```

---

## Response Envelope

All API responses use a consistent envelope:

**Success:**
```json
{ "ok": true, "data": { ... } }
```

**Error:**
```json
{
  "ok": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Entry 'ent_xyz' not found",
    "details": null
  }
}
```

---

## Block meta payloads

Block `meta` is `null` for text/markdown/code/quote blocks. For structured types:

**list block:**
```json
{ "meta": { "items": ["Item one", "Item two"] } }
```

**table block:**
```json
{
  "meta": {
    "headers": ["Name", "Value"],
    "rows": [["Alpha", "1"], ["Beta", "2"]]
  }
}
```

**code block:**
```json
{ "meta": { "language": "python" } }
```
