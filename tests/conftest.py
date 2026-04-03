"""Shared test fixtures for the SciEasy test suite."""

import pytest


@pytest.fixture()
def tmp_project_dir(tmp_path: pytest.TempPathFactory) -> "Path":  # noqa: F821
    """Create a temporary project directory structure for testing."""
    from pathlib import Path

    project_dir: Path = tmp_path / "test_project"  # type: ignore[operator]
    project_dir.mkdir()
    return project_dir
