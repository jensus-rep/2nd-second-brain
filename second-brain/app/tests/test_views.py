"""Tests for View and ViewItem API endpoints."""
import pytest
from fastapi.testclient import TestClient


def _create_entry(client: TestClient, title: str = "Entry") -> str:
    return client.post("/api/v1/entries", json={"title": title}).json()["data"]["id"]


def test_create_view(client: TestClient):
    resp = client.post("/api/v1/views", json={"title": "AI Overview", "type": "page"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["id"].startswith("view_")
    assert data["type"] == "page"


def test_list_views(client: TestClient):
    client.post("/api/v1/views", json={"title": "V1", "type": "page"})
    client.post("/api/v1/views", json={"title": "V2", "type": "collection"})
    resp = client.get("/api/v1/views")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


def test_get_view(client: TestClient):
    view_id = client.post("/api/v1/views", json={"title": "Detail Test", "type": "page"}).json()["data"]["id"]
    resp = client.get(f"/api/v1/views/{view_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Detail Test"


def test_update_view(client: TestClient):
    view_id = client.post("/api/v1/views", json={"title": "Original", "type": "page"}).json()["data"]["id"]
    resp = client.patch(f"/api/v1/views/{view_id}", json={"title": "Updated", "description": "desc"})
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated"


def test_delete_view(client: TestClient):
    view_id = client.post("/api/v1/views", json={"title": "Delete Me", "type": "page"}).json()["data"]["id"]
    assert client.delete(f"/api/v1/views/{view_id}").status_code == 204
    assert client.get(f"/api/v1/views/{view_id}").status_code == 404


def test_add_view_item(client: TestClient):
    entry_id = _create_entry(client, "For View")
    view_id = client.post("/api/v1/views", json={"title": "V", "type": "page"}).json()["data"]["id"]

    resp = client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": entry_id, "position": 0})
    assert resp.status_code == 201
    assert resp.json()["data"]["id"].startswith("vi_")


def test_add_view_item_invalid_entry(client: TestClient):
    view_id = client.post("/api/v1/views", json={"title": "V", "type": "page"}).json()["data"]["id"]
    resp = client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": "ent_doesntexist0", "position": 0})
    assert resp.status_code == 422


def test_remove_view_item(client: TestClient):
    entry_id = _create_entry(client)
    view_id = client.post("/api/v1/views", json={"title": "V", "type": "page"}).json()["data"]["id"]
    item_id = client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": entry_id, "position": 0}).json()["data"]["id"]

    assert client.delete(f"/api/v1/views/{view_id}/items/{item_id}").status_code == 204


def test_reorder_view_items(client: TestClient):
    e1 = _create_entry(client, "E1")
    e2 = _create_entry(client, "E2")
    view_id = client.post("/api/v1/views", json={"title": "Reorder", "type": "page"}).json()["data"]["id"]
    i1 = client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": e1, "position": 0}).json()["data"]["id"]
    i2 = client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": e2, "position": 1}).json()["data"]["id"]

    resp = client.post(f"/api/v1/views/{view_id}/items/reorder", json={"item_ids": [i2, i1]})
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert items[0]["id"] == i2
    assert items[0]["position"] == 0


def test_delete_entry_removes_from_view(client: TestClient):
    """Deleting an entry must cascade-remove its ViewItems."""
    entry_id = _create_entry(client, "WillDelete")
    view_id = client.post("/api/v1/views", json={"title": "V", "type": "page"}).json()["data"]["id"]
    client.post(f"/api/v1/views/{view_id}/items", json={"entry_id": entry_id, "position": 0})

    client.delete(f"/api/v1/entries/{entry_id}")

    view = client.get(f"/api/v1/views/{view_id}").json()["data"]
    assert len(view["items"]) == 0
