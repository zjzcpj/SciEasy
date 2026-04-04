"""ExternalAppBridge protocol and default file-exchange implementation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ExternalAppBridge(Protocol):
    """Structural protocol for bridging external GUI applications."""

    def prepare(self, inputs: dict[str, Any], exchange_dir: Path) -> None: ...
    def launch(self, command: str, exchange_dir: Path) -> Any: ...
    def watch(self, exchange_dir: Path, patterns: list[str]) -> list[Path]: ...
    def collect(self, output_files: list[Path]) -> dict[str, Any]: ...


class FileExchangeBridge:
    """Default bridge that serialises inputs to JSON/files and launches a subprocess."""

    def prepare(self, inputs: dict[str, Any], exchange_dir: Path) -> None:
        """Serialise *inputs* into *exchange_dir*."""
        exchange_dir.mkdir(parents=True, exist_ok=True)
        input_dir = exchange_dir / "inputs"
        input_dir.mkdir(exist_ok=True)

        manifest: dict[str, Any] = {}
        for key, value in inputs.items():
            from scieasy.core.proxy import ViewProxy

            if isinstance(value, ViewProxy):
                value = value.to_memory()

            # ADR-020-Add2: iterate Collection items one at a time.
            from scieasy.core.types.collection import Collection

            if isinstance(value, Collection):
                collection_dir = input_dir / key
                collection_dir.mkdir(exist_ok=True)
                item_paths = []
                for i, item in enumerate(value):
                    data = item.view().to_memory()
                    item_path = collection_dir / f"item_{i:04d}.json"
                    item_path.write_text(
                        json.dumps(data, default=str), encoding="utf-8"
                    )
                    item_paths.append(str(item_path))
                manifest[key] = {"type": "collection", "items": item_paths}
                continue

            if isinstance(value, (str, int, float, bool)):
                manifest[key] = {"type": "scalar", "value": value}
            elif isinstance(value, bytes):
                file_path = input_dir / f"{key}.bin"
                file_path.write_bytes(value)
                manifest[key] = {"type": "file", "path": str(file_path)}
            else:
                file_path = input_dir / f"{key}.json"
                file_path.write_text(
                    json.dumps(value, default=str), encoding="utf-8"
                )
                manifest[key] = {"type": "json", "path": str(file_path)}

        manifest_path = exchange_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # TODO(ADR-017): launch() must use spawn_block_process() factory.
    # TODO(ADR-019): launch() must return ProcessHandle.

    def launch(self, command: str, exchange_dir: Path) -> subprocess.Popen[bytes]:
        """Launch the external application with *command*."""
        return subprocess.Popen(
            [command, str(exchange_dir)],
            cwd=str(exchange_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def watch(self, exchange_dir: Path, patterns: list[str]) -> list[Path]:
        """Watch *exchange_dir* for output files matching *patterns*."""
        from scieasy.blocks.app.watcher import FileWatcher

        output_dir = exchange_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        watcher = FileWatcher(directory=output_dir, patterns=patterns, timeout=300)
        watcher.start()
        try:
            return watcher.wait_for_output()
        finally:
            watcher.stop()

    def collect(self, output_files: list[Path]) -> dict[str, Any]:
        """Collect results from *output_files* into a typed output mapping."""
        from scieasy.core.types.artifact import Artifact

        results: dict[str, Any] = {}
        for fp in output_files:
            artifact = Artifact(
                file_path=fp, mime_type=_guess_mime(fp), description=fp.name
            )
            results[fp.stem] = artifact
        return results


def _guess_mime(path: Path) -> str:
    """Guess MIME type from file extension."""
    mapping = {
        ".csv": "text/csv",
        ".tsv": "text/tab-separated-values",
        ".json": "application/json",
        ".txt": "text/plain",
        ".png": "image/png",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".pdf": "application/pdf",
    }
    return mapping.get(path.suffix.lower(), "application/octet-stream")
