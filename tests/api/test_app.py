"""Tests for FastAPI app factory and lifespan."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from fastapi import FastAPI

from scieasy.api.app import _lifespan, create_app
from scieasy.engine.runners.process_handle import ProcessRegistry


class TestCreateApp:
    """Tests for the create_app() factory function."""

    def test_returns_fastapi_instance(self) -> None:
        """create_app() returns a FastAPI app (no longer raises NotImplementedError)."""
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_title(self) -> None:
        """App has correct title metadata."""
        app = create_app()
        assert app.title == "SciEasy"

    def test_app_version(self) -> None:
        """App has the expected dev version string."""
        app = create_app()
        assert app.version == "0.1.0-dev"


class TestLifespan:
    """Tests for the _lifespan async context manager."""

    def test_lifespan_creates_registry(self) -> None:
        """Lifespan startup creates a ProcessRegistry on app.state."""

        async def _run() -> None:
            app = FastAPI()
            async with _lifespan(app):
                assert hasattr(app.state, "registry")
                assert isinstance(app.state.registry, ProcessRegistry)

        asyncio.run(_run())

    def test_lifespan_calls_terminate_all_on_shutdown(self) -> None:
        """Lifespan shutdown calls terminate_all on the registry."""
        called_with: dict[str, float] = {}

        async def _run() -> None:
            app = FastAPI()
            async with _lifespan(app):
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
        # The router's lifespan_context is set (FastAPI stores it internally).
        # We verify by checking the app can be used as an ASGI app
        # (basic structural check -- full integration tested via httpx).
        assert app.router.lifespan_context is not None


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
