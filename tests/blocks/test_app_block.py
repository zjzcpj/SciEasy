"""Tests for AppBlock — mock subprocess + file watcher."""

from __future__ import annotations

import time
from pathlib import Path
from threading import Thread

import pytest

from scieasy.blocks.app.bridge import FileExchangeBridge
from scieasy.blocks.app.watcher import FileWatcher
from scieasy.core.types.artifact import Artifact

# TODO(ADR-020): Update to pass Collection inputs, verify Collection outputs.


class TestFileWatcher:
    """FileWatcher — polling-based output detection."""

    def test_detects_new_file(self, tmp_path: Path) -> None:
        """Writing an output file after start() triggers detection."""
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        watcher = FileWatcher(directory=output_dir, patterns=["*.csv"], timeout=5, poll_interval=0.1)
        watcher.start()

        # Write a file in a background thread.
        def write_file() -> None:
            time.sleep(0.3)
            (output_dir / "result.csv").write_text("a,b\n1,2\n")

        t = Thread(target=write_file)
        t.start()

        files = watcher.wait_for_output()
        t.join()
        watcher.stop()

        assert len(files) == 1
        assert files[0].name == "result.csv"

    def test_timeout(self, tmp_path: Path) -> None:
        """No output within timeout raises TimeoutError."""
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        watcher = FileWatcher(directory=output_dir, patterns=["*.csv"], timeout=1, poll_interval=0.1)
        watcher.start()

        with pytest.raises(TimeoutError):
            watcher.wait_for_output()
        watcher.stop()

    def test_pattern_filtering(self, tmp_path: Path) -> None:
        """Only files matching the pattern are detected."""
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        watcher = FileWatcher(directory=output_dir, patterns=["*.txt"], timeout=5, poll_interval=0.1)
        watcher.start()

        def write_files() -> None:
            time.sleep(0.2)
            (output_dir / "data.csv").write_text("ignored")
            time.sleep(0.1)
            (output_dir / "result.txt").write_text("found")

        t = Thread(target=write_files)
        t.start()

        files = watcher.wait_for_output()
        t.join()
        watcher.stop()

        assert len(files) == 1
        assert files[0].suffix == ".txt"

    def test_not_started_raises(self, tmp_path: Path) -> None:
        watcher = FileWatcher(directory=tmp_path, patterns=["*"])
        with pytest.raises(RuntimeError, match="not been started"):
            watcher.wait_for_output()


class TestFileExchangeBridge:
    """FileExchangeBridge — prepare and collect steps."""

    def test_prepare_creates_manifest(self, tmp_path: Path) -> None:
        bridge = FileExchangeBridge()
        bridge.prepare({"value": 42, "name": "test"}, tmp_path)

        manifest = tmp_path / "manifest.json"
        assert manifest.exists()

        import json

        data = json.loads(manifest.read_text())
        assert data["value"]["type"] == "scalar"
        assert data["value"]["value"] == 42
        assert data["name"]["type"] == "scalar"
        assert data["name"]["value"] == "test"

    def test_prepare_handles_bytes(self, tmp_path: Path) -> None:
        bridge = FileExchangeBridge()
        bridge.prepare({"blob": b"binary data"}, tmp_path)

        import json

        data = json.loads((tmp_path / "manifest.json").read_text())
        assert data["blob"]["type"] == "file"
        blob_path = Path(data["blob"]["path"])
        assert blob_path.exists()
        assert blob_path.read_bytes() == b"binary data"

    def test_collect_creates_artifacts(self, tmp_path: Path) -> None:
        bridge = FileExchangeBridge()

        f1 = tmp_path / "output1.csv"
        f1.write_text("a,b\n1,2\n")
        f2 = tmp_path / "output2.png"
        f2.write_bytes(b"fake png")

        results = bridge.collect([f1, f2])
        assert "output1" in results
        assert "output2" in results
        assert isinstance(results["output1"], Artifact)
        assert results["output1"].mime_type == "text/csv"
        assert results["output2"].mime_type == "image/png"
