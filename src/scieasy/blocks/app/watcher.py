"""FileWatcher — polling-based output detection for AppBlock.

Uses a simple polling loop to detect new or modified files matching glob
patterns.  A watchdog-based implementation can be added later for lower
latency, but polling is reliable across all platforms and avoids adding
watchdog as a hard runtime dependency for the watcher alone.
"""

from __future__ import annotations

import fnmatch
import time
from pathlib import Path
from typing import Any


class ProcessExitedWithoutOutputError(RuntimeError):
    """Raised when the external process exits before producing expected output files."""

    pass


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
        poll_interval: float = 0.5,
        process_handle: Any | None = None,
    ) -> None:
        self.directory: Path = directory
        self.patterns: list[str] = patterns
        self.timeout: int | None = timeout
        self.poll_interval: float = poll_interval
        self._process_handle: Any | None = process_handle
        self._baseline: dict[Path, float] = {}
        self._running: bool = False

    def start(self) -> None:
        """Begin watching the directory for changes.

        Takes a snapshot of existing files so that only *new* or *modified*
        files are detected by :meth:`wait_for_output`.
        """
        self.directory.mkdir(parents=True, exist_ok=True)
        self._baseline = self._snapshot()
        self._running = True

    def wait_for_output(self) -> list[Path]:
        """Block until new output files are detected and return their paths.

        Raises :class:`ProcessExitedWithoutOutputError` if the watched process
        exits without producing output files.
        Raises :class:`TimeoutError` if *timeout* seconds elapse without
        detecting new matching files.
        """
        if not self._running:
            raise RuntimeError("FileWatcher has not been started.")

        deadline = None
        if self.timeout is not None:
            deadline = time.monotonic() + self.timeout

        while self._running:
            current = self._snapshot()
            new_files = self._diff(current)
            if new_files:
                return new_files

            # Check process liveness before sleeping.
            if self._process_handle is not None and not self._process_handle.is_alive() and not new_files:
                raise ProcessExitedWithoutOutputError(
                    f"External process (pid={self._process_handle.pid}) exited without producing output"
                )

            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"FileWatcher timed out after {self.timeout}s waiting for "
                    f"files matching {self.patterns} in {self.directory}"
                )
            time.sleep(self.poll_interval)

        return []

    def stop(self) -> None:
        """Stop watching and release resources."""
        self._running = False

    def _snapshot(self) -> dict[Path, float]:
        """Return a mapping of matched file paths to their mtime."""
        result: dict[Path, float] = {}
        if not self.directory.exists():
            return result
        for child in self.directory.iterdir():
            if child.is_file() and self._matches(child.name):
                result[child] = child.stat().st_mtime
        return result

    def _diff(self, current: dict[Path, float]) -> list[Path]:
        """Return files that are new or modified since the baseline."""
        new_files: list[Path] = []
        for path, mtime in current.items():
            if path not in self._baseline or mtime > self._baseline[path]:
                new_files.append(path)
        return sorted(new_files)

    def _matches(self, filename: str) -> bool:
        """Check if *filename* matches any of the watched patterns."""
        return any(fnmatch.fnmatch(filename, pat) for pat in self.patterns)
