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

    deleted = client.delete(f"/api/projects/{first_payload['id']}")
    assert deleted.status_code == 204
    assert not Path(first_payload["path"]).exists()


def test_browse_directory_endpoint(client: TestClient) -> None:
    """Browse directory endpoint should return a path or null without error."""
    from unittest.mock import patch

    with patch("scieasy.api.routes.projects._pick_directory", return_value="/tmp/picked"):
        resp = client.post("/api/projects/browse-directory")
        assert resp.status_code == 200
        assert resp.json()["path"] == "/tmp/picked"

    with patch("scieasy.api.routes.projects._pick_directory", return_value=None):
        resp = client.post("/api/projects/browse-directory")
        assert resp.status_code == 200
        assert resp.json()["path"] is None


def test_browse_files_endpoint(client: TestClient) -> None:
    """Browse files endpoint should return a list of paths (#208)."""
    from unittest.mock import patch

    with patch(
        "scieasy.api.routes.projects._pick_files",
        return_value=["/tmp/a.csv", "/tmp/b.csv"],
    ):
        resp = client.post("/api/projects/browse-files")
        assert resp.status_code == 200
        data = resp.json()
        assert "paths" in data
        assert data["paths"] == ["/tmp/a.csv", "/tmp/b.csv"]

    with patch("scieasy.api.routes.projects._pick_files", return_value=[]):
        resp = client.post("/api/projects/browse-files")
        assert resp.status_code == 200
        assert resp.json()["paths"] == []


def test_pick_files_returns_empty_on_exception() -> None:
    """_pick_files should return an empty list when tkinter is unavailable."""
    from unittest.mock import patch

    with patch.dict("sys.modules", {"tkinter": None}):
        from scieasy.api.routes.projects import _pick_files

        result = _pick_files()
        assert result == []
