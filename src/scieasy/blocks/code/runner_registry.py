"""RunnerRegistry — maps language string to CodeRunner class."""

from __future__ import annotations

from typing import Any


class RunnerRegistry:
    """Registry that maps language identifiers to :class:`CodeRunner` classes."""

    def __init__(self) -> None:
        self._runners: dict[str, type] = {}

    def register(self, language: str, runner_class: type) -> None:
        """Register *runner_class* for the given *language*."""
        raise NotImplementedError

    def get(self, language: str) -> Any:
        """Return the runner class registered for *language*."""
        raise NotImplementedError

    def all_runners(self) -> dict[str, type]:
        """Return a copy of the full language-to-runner mapping."""
        raise NotImplementedError
