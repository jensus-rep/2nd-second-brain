"""Tests for Update Matrix engine — typed operations, temp_id resolution, strict mode."""
import pytest
from fastapi.testclient import TestClient


def _matrix(ops: list, mode: str = "strict", txn_id: str = "test_txn") -> dict:
    return {"schema_version": "1.0", "transaction_id": txn_id, "mode": mode, "operations": ops}


def test_create_entry_via_matrix(client: TestClient):
    body = _matrix([{
        "op": "create_entry",
        "temp_id": "tmp_e1",
        "data": {"title": "Matrix Entry", "status": "active"},
    }])
    resp = client.post("/api/v1/import/update-matrix", json=body)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "applied"
    assert "tmp_e1" in data["temp_id_map"]
    final_id = data["temp_id_map"]["tmp_e1"]
    assert final_id.startswith("ent_")
    assert data["counts"]["created"] == 1


def test_temp_id_reference_in_same_matrix(client: TestClient):
    """A block append referencing a temp_id from a prior create_entry must resolve correctly."""
    body = _matrix([
        {
            "op": "create_entry",
            "temp_id": "tmp_e1",
            "data": {"title": "With Block", "status": "active"},
        },
        {
            "op": "append_block",
            "entry_ref": "tmp_e1",
            "data": {"type": "markdown", "content": "# Hello", "position": 0},
        },
    ])
    resp = client.post("/api/v1/import/update-matrix", json=body)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "applied"
    assert data["counts"]["created"] == 2

    entry_id = data["temp_id_map"]["tmp_e1"]
    entry = client.get(f"/api/v1/entries/{entry_id}").json()["data"]
    assert len(entry["blocks"]) == 1
    assert entry["blocks"][0]["content"] == "# Hello"


def test_strict_mode_rollback_on_failure(client: TestClient):
    """In strict mode, a failure in any op rolls back the whole transaction."""
    body = _matrix([
        {
            "op": "create_entry",
            "temp_id": "tmp_good",
            "data": {"title": "Good Entry"},
        },
        {
            "op": "update_entry",
            "entry_id": "ent_doesNotExist0",  # will fail
            "patch": {"title": "Fail"},
        },
    ], mode="strict")
    resp = client.post("/api/v1/import/update-matrix", json=body)
    data = resp.json()["data"]
    assert data["status"] == "rejected"
    # Good entry must NOT have been committed
    assert "tmp_good" not in data["temp_id_map"] or data["counts"]["created"] == 0


def test_best_effort_partial_apply(client: TestClient):
    """In best_effort mode, valid ops succeed and invalid ops are reported per-op."""
    body = _matrix([
        {
            "op": "create_entry",
            "temp_id": "tmp_ok",
            "data": {"title": "Best Effort Entry"},
        },
        {
            "op": "update_entry",
            "entry_id": "ent_doesNotExist0",
            "patch": {"title": "X"},
        },
    ], mode="best_effort")
    resp = client.post("/api/v1/import/update-matrix", json=body)
    data = resp.json()["data"]
    assert data["status"] == "partial"
    ops = {o["index"]: o for o in data["operations"]}
    assert ops[0]["status"] == "applied"
    assert ops[1]["status"] == "rejected"
    assert data["counts"]["created"] >= 1


def test_link_entries_operation(client: TestClient):
    body = _matrix([
        {"op": "create_entry", "temp_id": "tmp_src", "data": {"title": "Source"}},
        {"op": "create_entry", "temp_id": "tmp_tgt", "data": {"title": "Target"}},
        {
            "op": "link_entries",
            "data": {
                "source_entry_id": "tmp_src",
                "target_entry_id": "tmp_tgt",
                "relation_type": "related",
                "position": 0,
            },
        },
    ])
    resp = client.post("/api/v1/import/update-matrix", json=body)
    data = resp.json()["data"]
    assert data["status"] == "applied"
    assert data["counts"]["created"] == 3  # 2 entries + 1 relation

    src_id = data["temp_id_map"]["tmp_src"]
    entry = client.get(f"/api/v1/entries/{src_id}").json()["data"]
    assert len(entry["relations"]) == 1
    assert entry["relations"][0]["relation_type"] == "related"


def test_reorder_blocks_operation(client: TestClient):
    # Create entry + 2 blocks
    setup = _matrix([
        {"op": "create_entry", "temp_id": "tmp_e", "data": {"title": "Reorder Test"}},
        {"op": "append_block", "entry_ref": "tmp_e", "data": {"type": "text", "content": "A", "position": 0}},
        {"op": "append_block", "entry_ref": "tmp_e", "data": {"type": "text", "content": "B", "position": 1}},
    ])
    setup_resp = client.post("/api/v1/import/update-matrix", json=setup).json()
    entry_id = setup_resp["data"]["temp_id_map"]["tmp_e"]

    blocks = client.get(f"/api/v1/entries/{entry_id}").json()["data"]["blocks"]
    b_ids = [b["id"] for b in sorted(blocks, key=lambda x: x["position"])]

    # Reverse order
    reorder = _matrix([{
        "op": "reorder_blocks",
        "entry_id": entry_id,
        "block_ids": list(reversed(b_ids)),
    }])
    resp = client.post("/api/v1/import/update-matrix", json=reorder)
    assert resp.json()["data"]["status"] == "applied"

    reordered = client.get(f"/api/v1/entries/{entry_id}").json()["data"]["blocks"]
    assert reordered[0]["id"] == b_ids[1]


def test_delete_entry_operation(client: TestClient):
    setup = _matrix([{"op": "create_entry", "temp_id": "tmp_del", "data": {"title": "To Delete"}}])
    entry_id = client.post("/api/v1/import/update-matrix", json=setup).json()["data"]["temp_id_map"]["tmp_del"]

    del_matrix = _matrix([{"op": "delete_entry", "entry_id": entry_id}])
    resp = client.post("/api/v1/import/update-matrix", json=del_matrix)
    assert resp.json()["data"]["status"] == "applied"
    assert client.get(f"/api/v1/entries/{entry_id}").status_code == 404


def test_archive_entry_operation(client: TestClient):
    setup = _matrix([{"op": "create_entry", "temp_id": "tmp_arc", "data": {"title": "Archive Me", "status": "active"}}])
    entry_id = client.post("/api/v1/import/update-matrix", json=setup).json()["data"]["temp_id_map"]["tmp_arc"]

    arc = _matrix([{"op": "archive_entry", "entry_id": entry_id}])
    client.post("/api/v1/import/update-matrix", json=arc)

    entry = client.get(f"/api/v1/entries/{entry_id}").json()["data"]
    assert entry["status"] == "archived"
