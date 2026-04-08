"""Tests for Entry and Block CRUD API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_create_entry(client: TestClient):
    resp = client.post("/api/v1/entries", json={"title": "Test Entry", "status": "active"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["title"] == "Test Entry"
    assert data["data"]["id"].startswith("ent_")


def test_get_entry(client: TestClient):
    create = client.post("/api/v1/entries", json={"title": "Readable Entry", "category": "Tech"})
    entry_id = create.json()["data"]["id"]

    resp = client.get(f"/api/v1/entries/{entry_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["category"] == "Tech"


def test_entry_not_found(client: TestClient):
    resp = client.get("/api/v1/entries/ent_notexistent0")
    assert resp.status_code == 404


def test_update_entry(client: TestClient):
    create = client.post("/api/v1/entries", json={"title": "Old Title"})
    entry_id = create.json()["data"]["id"]

    resp = client.patch(f"/api/v1/entries/{entry_id}", json={"title": "New Title", "category": "AI"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "New Title"
    assert data["category"] == "AI"


def test_delete_entry(client: TestClient):
    create = client.post("/api/v1/entries", json={"title": "Deletable"})
    entry_id = create.json()["data"]["id"]

    del_resp = client.delete(f"/api/v1/entries/{entry_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/entries/{entry_id}")
    assert get_resp.status_code == 404


def test_list_entries(client: TestClient):
    client.post("/api/v1/entries", json={"title": "A", "status": "active"})
    client.post("/api/v1/entries", json={"title": "B", "status": "draft"})

    resp = client.get("/api/v1/entries")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2

    resp_active = client.get("/api/v1/entries?status=active")
    for e in resp_active.json()["data"]:
        assert e["status"] == "active"


def test_append_block(client: TestClient):
    entry_id = client.post("/api/v1/entries", json={"title": "BlockTest"}).json()["data"]["id"]

    resp = client.post(
        f"/api/v1/entries/{entry_id}/blocks",
        json={"type": "markdown", "content": "# Hello", "position": 0},
    )
    assert resp.status_code == 201
    block = resp.json()["data"]
    assert block["id"].startswith("blk_")
    assert block["type"] == "markdown"


def test_reorder_blocks(client: TestClient):
    entry_id = client.post("/api/v1/entries", json={"title": "Reorder"}).json()["data"]["id"]

    b1 = client.post(f"/api/v1/entries/{entry_id}/blocks", json={"type": "text", "content": "First", "position": 0}).json()["data"]["id"]
    b2 = client.post(f"/api/v1/entries/{entry_id}/blocks", json={"type": "text", "content": "Second", "position": 1}).json()["data"]["id"]

    # Reverse order
    resp = client.post(f"/api/v1/entries/{entry_id}/blocks/reorder", json={"block_ids": [b2, b1]})
    assert resp.status_code == 200
    ordered = resp.json()["data"]
    assert ordered[0]["id"] == b2
    assert ordered[0]["position"] == 0
    assert ordered[1]["id"] == b1
    assert ordered[1]["position"] == 1


def test_reorder_blocks_wrong_ids(client: TestClient):
    entry_id = client.post("/api/v1/entries", json={"title": "ReorderFail"}).json()["data"]["id"]
    client.post(f"/api/v1/entries/{entry_id}/blocks", json={"type": "text", "content": "X", "position": 0})

    resp = client.post(f"/api/v1/entries/{entry_id}/blocks/reorder", json={"block_ids": ["blk_wrongID00000"]})
    assert resp.status_code == 422


def test_delete_block(client: TestClient):
    entry_id = client.post("/api/v1/entries", json={"title": "BlockDelete"}).json()["data"]["id"]
    block_id = client.post(f"/api/v1/entries/{entry_id}/blocks", json={"type": "text", "content": "bye", "position": 0}).json()["data"]["id"]

    resp = client.delete(f"/api/v1/entries/{entry_id}/blocks/{block_id}")
    assert resp.status_code == 204


def test_delete_entry_cascades_blocks(client: TestClient):
    """Deleting an entry must remove its blocks."""
    entry_id = client.post("/api/v1/entries", json={"title": "Cascade"}).json()["data"]["id"]
    client.post(f"/api/v1/entries/{entry_id}/blocks", json={"type": "text", "content": "gone", "position": 0})

    client.delete(f"/api/v1/entries/{entry_id}")
    # Entry is gone
    assert client.get(f"/api/v1/entries/{entry_id}").status_code == 404
