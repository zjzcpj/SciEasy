"""Tests for project management endpoints."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient


def test_project_crud_and_path_opening(client: TestClient, project_parent: Path) -> None:
    """Projects should be creatable, listable, updatable, openable, and deletable."""
    first = client.post(
        "/api/projects/",
        json={"name": "Alpha", "description": "first", "path": str(project_parent)},
    )
    second = client.post(
        "/api/projects/",
        json={"name": "Beta", "description": "second", "path": str(project_parent)},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()

    workflow = {
        "id": "demo-workflow",
        "nodes": [],
        "edges": [],
        "metadata": {},
    }
    create_workflow = client.post("/api/workflows/", json=workflow)
    assert create_workflow.status_code == 200

    listed = client.get("/api/projects/")
    assert listed.status_code == 200
    projects = {entry["name"]: entry for entry in listed.json()}
    assert projects["Beta"]["workflow_count"] == 1

    updated = client.put(
        f"/api/projects/{second_payload['id']}",
        json={"name": "Beta Updated", "description": "renamed"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Beta Updated"

    by_path = client.get(f"/api/projects/{quote(second_payload['path'], safe='')}")
    assert by_path.status_code == 200
    assert by_path.json()["id"] == second_payload["id"]

    # Verify data/exchange is created alongside other data subdirs (#565).
    project_path = Path(second_payload["path"])
    assert (project_path / "data" / "exchange").is_dir()

    deleted = client.delete(f"/api/projects/{first_payload['id']}")
    assert deleted.status_code == 204
    assert not Path(first_payload["path"]).exists()
