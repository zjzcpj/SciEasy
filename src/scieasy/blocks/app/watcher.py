"""FileWatcher — watchdog-based output detection for AppBlock."""

from __future__ import annotations

from pathlib import Path


class FileWatcher:
    """Watches a directory for new or modified files matching glob patterns.

    Used by :class:`AppBlock` to detect when an external application has
    produced output files.
    """

    def __init__(
        self,
        directory: Path,
        patterns: list[str],
        timeout: int | None = None,
    ) -> None:
        self.directory: Path = directory
        self.patterns: list[str] = patterns
        self.timeout: int | None = timeout

    def start(self) -> None:
        """Begin watching the directory for changes."""
        raise NotImplementedError

    def wait_for_output(self) -> list[Path]:
        """Block until output files are detected and return their paths."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop watching and release resources."""
        raise NotImplementedError
