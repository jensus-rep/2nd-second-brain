# Update Engine

## Purpose

The Update Matrix engine is the single authorized path for all mutations.
It enforces explicit, typed, traceable operations with transactional guarantees.

## Architecture

```
UpdateMatrix (input)
    │
    ▼
update_matrix_service.apply_update_matrix()
    │
    ├── _ExecutionContext  (temp_id_map, counters)
    │
    ├── for each operation:
    │       │
    │       ├── resolve entry_ref / entry_id / view_id via temp_id_map
    │       ├── call typed handler (_handle_create_entry, etc.)
    │       ├── session.flush()  where flush is needed (create with temp_id)
    │       └── record OperationResult
    │
    ├── on strict failure:
    │       session.rollback()
    │       mark remaining ops as skipped
    │
    ├── on success / best_effort partial:
    │       session.commit()
    │
    └── _write_log() → UpdateLog (always, even on failure)
```

## Transaction Modes

### strict (default)
- All operations execute in a single DB transaction
- Any failure triggers immediate rollback of all prior ops
- Returns `status: "rejected"`, no changes persist
- Remaining operations are marked `"skipped"`

### best_effort
- Operations execute sequentially
- Failed ops are recorded with an error message
- Successful ops are committed
- Returns `status: "partial"` if any op failed, `"applied"` if all succeeded

## temp_id Resolution

The `_ExecutionContext.temp_id_map` maps `temp_id` → final server ID.

Rules:
1. A `create_entry` op with `temp_id: "tmp_x"` causes `session.flush()` to populate the real ID
2. The mapping `tmp_x → ent_abc123` is recorded in `temp_id_map`
3. Any later op using `entry_ref: "tmp_x"` resolves to `ent_abc123`
4. Works for both entries (`create_entry`) and views (`create_view`)
5. temp_ids are scoped to one transaction — they do not persist

## UpdateLog

Every matrix application, successful or not, writes an `UpdateLog` record:

| Field | Content |
|---|---|
| `id` | `ulog_` prefixed server ID |
| `applied_at` | UTC timestamp |
| `source_type` | `manual`, `agent`, `llm`, or `import` |
| `payload_json` | Full serialized `UpdateMatrix` |
| `result_json` | Full serialized `UpdateMatrixResult` |
| `status` | `applied`, `rejected`, or `partial` |
| `created_entities` | Count of created rows |
| `updated_entities` | Count of updated rows |
| `deleted_entities` | Count of deleted rows |

Log writes are best-effort (a logging failure never corrupts the response).

## Reference Validation

- All `entry_id`, `source_entry_id`, `target_entry_id`, `view_id` references are validated before the op modifies data
- Invalid references raise `LookupError` which is caught by the engine
- In strict mode this triggers rollback
- References may be temp_ids from earlier ops in the same transaction

## Explicit Deletion Rule

Deletion is NEVER implicit. The following ops are the only way to remove data:

| Op | What it deletes |
|---|---|
| `delete_entry` | Entry + cascades Blocks, Relations, ViewItems |
| `delete_block` | Single block |
| `unlink_relation` | Single relation |
| `delete_view` | View + cascades ViewItems |
| `remove_view_item` | Single ViewItem |

A snapshot import with missing IDs does NOT delete those entities.
An update_entry patch with missing fields does NOT nullify those fields.

## Reorder Validation

`reorder_blocks` and `reorder_view_items` require the complete set of IDs:

- The provided `block_ids` (or `item_ids`) must exactly match the current set
- Extra IDs → error
- Missing IDs → error
- This ensures no block is accidentally dropped from the ordering

## Handlers Dispatch Table

```python
_HANDLERS = {
    "create_entry":       _handle_create_entry,
    "update_entry":       _handle_update_entry,
    "delete_entry":       _handle_delete_entry,
    "archive_entry":      _handle_archive_entry,
    "append_block":       _handle_append_block,
    "insert_block":       _handle_insert_block,
    "update_block":       _handle_update_block,
    "delete_block":       _handle_delete_block,
    "reorder_blocks":     _handle_reorder_blocks,
    "link_entries":       _handle_link_entries,
    "unlink_relation":    _handle_unlink_relation,
    "create_view":        _handle_create_view,
    "update_view":        _handle_update_view,
    "delete_view":        _handle_delete_view,
    "add_view_item":      _handle_add_view_item,
    "remove_view_item":   _handle_remove_view_item,
    "reorder_view_items": _handle_reorder_view_items,
}
```

Each handler receives `(operation, session, ctx)` and raises `LookupError` or `ValueError` on failure.
