"""Tests for the filesystem browsing and reveal API endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


class TestProjectTree:
    """Tests for GET /api/projects/{project_id}/tree."""

    def test_list_root(self, client: TestClient, opened_project: Path) -> None:
        """Root listing returns project-standard directories."""
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree")
        assert resp.status_code == 200
        data = resp.json()
        names = [e["name"] for e in data["entries"]]
        # Standard project directories created by create_project
        assert "workflows" in names
        assert "blocks" in names
        assert "data" in names

    def test_directories_before_files(self, client: TestClient, opened_project: Path) -> None:
        """Directories are listed before files, both alphabetical."""
        # Create a file in the project root
        (opened_project / "readme.txt").write_text("hello")
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree")
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        # All directories come before all files
        dir_indices = [i for i, e in enumerate(entries) if e["type"] == "directory"]
        file_indices = [i for i, e in enumerate(entries) if e["type"] == "file"]
        if dir_indices and file_indices:
            assert max(dir_indices) < min(file_indices)

    def test_subdirectory_listing(self, client: TestClient, opened_project: Path) -> None:
        """Listing a subdirectory returns its contents."""
        (opened_project / "data" / "raw" / "sample.csv").write_text("a,b\n1,2")
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree", params={"path": "data/raw"})
        assert resp.status_code == 200
        names = [e["name"] for e in resp.json()["entries"]]
        assert "sample.csv" in names

    def test_file_size_returned(self, client: TestClient, opened_project: Path) -> None:
        """File entries include a size field."""
        content = "test content"
        (opened_project / "test.txt").write_text(content)
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree")
        entries = resp.json()["entries"]
        txt = next(e for e in entries if e["name"] == "test.txt")
        assert txt["size"] is not None
        assert txt["size"] > 0

    def test_reject_path_traversal(self, client: TestClient, opened_project: Path) -> None:
        """Paths containing '..' are rejected."""
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree", params={"path": "../"})
        assert resp.status_code == 400

    def test_nonexistent_directory(self, client: TestClient, opened_project: Path) -> None:
        """Listing a path that does not exist returns 404."""
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree", params={"path": "nonexistent"})
        assert resp.status_code == 404

    def test_unknown_project(self, client: TestClient) -> None:
        """Unknown project ID returns 404."""
        resp = client.get("/api/projects/no-such-project/tree")
        assert resp.status_code == 404

    def test_hidden_files_excluded(self, client: TestClient, opened_project: Path) -> None:
        """Files and directories starting with '.' are not listed."""
        (opened_project / ".hidden_dir").mkdir()
        (opened_project / ".hidden_file").write_text("secret")
        runtime = client.app.state.runtime
        project_id = runtime.active_project.id

        resp = client.get(f"/api/projects/{project_id}/tree")
        names = [e["name"] for e in resp.json()["entries"]]
        assert ".hidden_dir" not in names
        assert ".hidden_file" not in names


class TestRevealInExplorer:
    """Tests for POST /api/filesystem/reveal."""

    def test_nonexistent_path(self, client: TestClient) -> None:
        """Reveal with a nonexistent path returns 404."""
        resp = client.post(
            "/api/filesystem/reveal",
            json={"path": "/tmp/definitely-does-not-exist-xyz"},
        )
        assert resp.status_code == 404

    def test_reveal_existing_path(self, client: TestClient, opened_project: Path, monkeypatch: object) -> None:
        """Reveal with a valid path returns 200 (mocked subprocess)."""
        import subprocess

        calls: list[list[str]] = []

        class FakePopen:
            def __init__(self, args: list[str], **_kwargs: object) -> None:
                calls.append(args)

        import scieasy.api.routes.filesystem as fs_mod

        # Monkeypatch subprocess.Popen in the filesystem module
        original_popen = subprocess.Popen
        fs_mod.subprocess.Popen = FakePopen  # type: ignore[assignment]
        try:
            resp = client.post(
                "/api/filesystem/reveal",
                json={"path": str(opened_project)},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"
            assert len(calls) == 1
        finally:
            fs_mod.subprocess.Popen = original_popen  # type: ignore[assignment]
