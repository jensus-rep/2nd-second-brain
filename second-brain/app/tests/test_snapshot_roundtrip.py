"""Tests for Snapshot export/import round-trip behavior."""
import pytest
from fastapi.testclient import TestClient


def _create_entry(client: TestClient, title: str, category: str = "Test") -> str:
    return client.post("/api/v1/entries", json={"title": title, "category": category}).json()["data"]["id"]


def test_snapshot_export_empty(client: TestClient):
    resp = client.get("/api/v1/export/snapshot")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["schema_version"] == "1.0"
    assert "entries" in data
    assert "views" in data


def test_snapshot_export_contains_entries(client: TestClient):
    _create_entry(client, "Alpha")
    _create_entry(client, "Beta")
    data = client.get("/api/v1/export/snapshot").json()["data"]
    titles = [e["title"] for e in data["entries"]]
    assert "Alpha" in titles
    assert "Beta" in titles


def test_snapshot_roundtrip_entry_with_blocks(client: TestClient):
    """Export then re-import should upsert without creating duplicates."""
    entry_id = _create_entry(client, "Round Trip")
    client.post(f"/api/v1/entries/{entry_id}/blocks", json={"type": "markdown", "content": "# Test", "position": 0})

    snapshot = client.get("/api/v1/export/snapshot").json()["data"]
    result = client.post("/api/v1/import/snapshot", json=snapshot).json()["data"]

    # No new entries created — all existing (upsert updated them)
    assert result["created_entries"] == 0
    assert result["updated_entries"] >= 1

    # Entry still accessible with blocks intact
    entry = client.get(f"/api/v1/entries/{entry_id}").json()["data"]
    assert entry["title"] == "Round Trip"
    assert len(entry["blocks"]) == 1


def test_snapshot_import_is_non_destructive(client: TestClient):
    """An empty snapshot must not delete existing entries."""
    _create_entry(client, "Should Survive")

    empty_snapshot = {"schema_version": "1.0", "entries": [], "views": []}
    client.post("/api/v1/import/snapshot", json=empty_snapshot)

    entries = client.get("/api/v1/entries").json()["data"]
    assert any(e["title"] == "Should Survive" for e in entries)


def test_snapshot_import_new_entries(client: TestClient):
    """Importing a snapshot with new IDs creates them."""
    from app.core.ids import entry_id as gen_id, block_id as gen_block_id
    from app.core.clock import utcnow

    now = utcnow().isoformat()
    new_eid = gen_id()
    new_bid = gen_block_id()

    snapshot = {
        "schema_version": "1.0",
        "entries": [{
            "id": new_eid,
            "title": "Imported Entry",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "blocks": [{
                "id": new_bid,
                "type": "text",
                "content": "Imported block",
                "position": 0,
                "created_at": now,
                "updated_at": now,
            }],
            "relations": [],
        }],
        "views": [],
    }
    result = client.post("/api/v1/import/snapshot", json=snapshot).json()["data"]
    assert result["created_entries"] == 1

    entry = client.get(f"/api/v1/entries/{new_eid}").json()["data"]
    assert entry["title"] == "Imported Entry"
    assert len(entry["blocks"]) == 1


def test_snapshot_with_views(client: TestClient):
    entry_id = _create_entry(client, "View Entry")
    view_resp = client.post("/api/v1/views", json={"title": "Snap View", "type": "page"}).json()["data"]
    view_id = view_resp["id"]
    client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": entry_id, "position": 0})

    snapshot = client.get("/api/v1/export/snapshot").json()["data"]
    view_in_snap = next((v for v in snapshot["views"] if v["id"] == view_id), None)
    assert view_in_snap is not None
    assert any(i["entry_id"] == entry_id for i in view_in_snap["items"])
