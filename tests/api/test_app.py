"""Tests for FastAPI app factory and lifespan."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scieasy.api.app import create_app, lifespan
from scieasy.engine.runners.process_handle import ProcessRegistry


class TestCreateApp:
    """Tests for the create_app() factory function."""

    def test_returns_fastapi_instance(self) -> None:
        """create_app() returns a FastAPI app."""
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_title(self) -> None:
        """App has correct title metadata."""
        app = create_app()
        assert app.title == "SciEasy API"

    def test_app_version(self) -> None:
        """App has the expected version string."""
        app = create_app()
        assert app.version == "0.1.0"


class TestLifespan:
    """Tests for the lifespan async context manager."""

    def test_lifespan_creates_registry(self) -> None:
        """Lifespan startup creates a ProcessRegistry on app.state."""

        async def _run() -> None:
            app = FastAPI()
            async with lifespan(app):
                assert hasattr(app.state, "registry")
                assert isinstance(app.state.registry, ProcessRegistry)

        asyncio.run(_run())

    def test_lifespan_creates_runtime(self) -> None:
        """Lifespan startup creates an ApiRuntime on app.state."""
        from scieasy.api.runtime import ApiRuntime

        async def _run() -> None:
            app = FastAPI()
            async with lifespan(app):
                assert hasattr(app.state, "runtime")
                assert isinstance(app.state.runtime, ApiRuntime)

        asyncio.run(_run())

    def test_lifespan_calls_terminate_all_on_shutdown(self) -> None:
        """Lifespan shutdown calls terminate_all on the registry."""
        called_with: dict[str, float] = {}

        async def _run() -> None:
            app = FastAPI()
            async with lifespan(app):
                registry = app.state.registry

                def mock_terminate_all(grace_period_sec: float = 5.0) -> None:
                    called_with["grace_period_sec"] = grace_period_sec

                registry.terminate_all = mock_terminate_all
            # After exiting context, terminate_all should have been called

        asyncio.run(_run())
        assert "grace_period_sec" in called_with
        assert called_with["grace_period_sec"] == 5.0

    def test_lifespan_integrated_with_create_app(self) -> None:
        """The app from create_app() has the lifespan wired in."""
        app = create_app()
        assert app.router.lifespan_context is not None


class TestStaticMount:
    """Tests for conditional SPA static file mounting."""

    def test_no_static_mount_when_dir_absent(self) -> None:
        """In dev mode (no static dir), root redirects to /docs."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"

    def test_static_mount_when_dir_exists(self, tmp_path: Path, monkeypatch: object) -> None:
        """When static dir exists, SPA mount serves index.html."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        (static_dir / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

        import scieasy.api.app as app_mod

        monkeypatch.setattr(
            app_mod, "SPAStaticFiles", __import__("scieasy.api.spa", fromlist=["SPAStaticFiles"]).SPAStaticFiles
        )  # type: ignore[union-attr]
        original_create_app = app_mod.create_app

        def patched_create_app() -> FastAPI:
            # Temporarily make Path(__file__).parent / "static" point to our tmp dir
            import unittest.mock

            with unittest.mock.patch.object(Path, "exists", side_effect=lambda self=None: True):
                pass
            return original_create_app()

        # Simpler: directly check that a Mount named "spa" exists when static dir exists
        from starlette.routing import Mount

        # Create the static dir at the expected location
        expected_static = Path(app_mod.__file__).parent / "static"  # type: ignore[arg-type]
        expected_static.mkdir(exist_ok=True)
        (expected_static / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
        try:
            app = create_app()
            spa_mounts = [r for r in app.routes if isinstance(r, Mount) and r.name == "spa"]
            assert len(spa_mounts) == 1
        finally:
            import shutil

            shutil.rmtree(expected_static, ignore_errors=True)


class TestGetProcessRegistry:
    """Tests for the get_process_registry dependency function."""

    def test_returns_registry_from_app_state(self) -> None:
        """Returns the ProcessRegistry when it exists on app.state."""
        from scieasy.api.deps import get_process_registry

        mock_request = MagicMock()
        mock_request.app.state.registry = ProcessRegistry()
        result = get_process_registry(mock_request)
        assert isinstance(result, ProcessRegistry)

    def test_raises_runtime_error_when_not_initialized(self) -> None:
        """Raises RuntimeError when registry is not on app.state."""
        import pytest

        from scieasy.api.deps import get_process_registry

        mock_request = MagicMock()
        # Simulate state without registry attribute
        mock_request.app.state = MagicMock(spec=[])

        with pytest.raises(RuntimeError, match="ProcessRegistry not initialized"):
            get_process_registry(mock_request)
