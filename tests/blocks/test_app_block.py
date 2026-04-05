"""Tests for AppBlock — mock subprocess + file watcher."""

from __future__ import annotations

import time
from pathlib import Path
from threading import Thread

import pytest

from scieasy.blocks.app.bridge import FileExchangeBridge
from scieasy.blocks.app.watcher import FileWatcher
from scieasy.core.types.artifact import Artifact


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


class TestAppBlockExchangeDir:
    """#68: Exchange directory location — project workspace vs tempfile fallback."""

    def test_exchange_dir_uses_project_workspace(self, tmp_path: Path) -> None:
        """When project_dir and block_id are in config, exchange dir is in project workspace."""
        from unittest.mock import MagicMock, patch

        from scieasy.blocks.app.app_block import AppBlock
        from scieasy.blocks.base.config import BlockConfig
        from scieasy.blocks.base.state import BlockState

        block = AppBlock()
        # Transition to READY so run() can transition to RUNNING.
        block.transition(BlockState.READY)

        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        config = BlockConfig(
            params={
                "app_command": "echo hello",
                "project_dir": str(project_dir),
                "block_id": "block_123",
            }
        )

        expected_dir = project_dir / "data" / "exchange" / "block_123"

        # Patch bridge and watcher to avoid real subprocess execution.
        with (
            patch("scieasy.blocks.app.app_block.FileExchangeBridge") as mock_bridge_cls,
            patch("scieasy.blocks.app.app_block.subprocess") as _mock_sub,
        ):
            mock_bridge = MagicMock()
            mock_bridge_cls.return_value = mock_bridge
            # Make bridge.launch return a mock process.
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.pid = 12345
            mock_bridge.launch.return_value = mock_proc

            # Patch FileWatcher to return fake output files immediately.
            with patch("scieasy.blocks.app.watcher.FileWatcher") as mock_watcher_cls:
                mock_watcher = MagicMock()
                mock_watcher_cls.return_value = mock_watcher
                fake_output = tmp_path / "result.csv"
                fake_output.write_text("a,b\n1,2\n")
                mock_watcher.wait_for_output.return_value = [fake_output]

                mock_bridge.collect.return_value = {}

                block.run(inputs={}, config=config)

            # Verify bridge.prepare was called with the project workspace path.
            call_args = mock_bridge.prepare.call_args
            actual_exchange_dir = call_args[0][1]  # second positional arg
            assert actual_exchange_dir == expected_dir

    def test_exchange_dir_falls_back_to_tempfile(self, tmp_path: Path) -> None:
        """When project_dir is not set, exchange dir falls back to tempfile."""
        from unittest.mock import MagicMock, patch

        from scieasy.blocks.app.app_block import AppBlock
        from scieasy.blocks.base.config import BlockConfig
        from scieasy.blocks.base.state import BlockState

        block = AppBlock()
        # Transition to READY so run() can transition to RUNNING.
        block.transition(BlockState.READY)

        config = BlockConfig(
            params={
                "app_command": "echo hello",
            }
        )

        with (
            patch("scieasy.blocks.app.app_block.FileExchangeBridge") as mock_bridge_cls,
            patch("scieasy.blocks.app.app_block.subprocess") as _mock_sub,
            patch(
                "scieasy.blocks.app.app_block.tempfile.mkdtemp", return_value=str(tmp_path / "fallback")
            ) as mock_mkdtemp,
        ):
            mock_bridge = MagicMock()
            mock_bridge_cls.return_value = mock_bridge
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.pid = 12345
            mock_bridge.launch.return_value = mock_proc

            with patch("scieasy.blocks.app.watcher.FileWatcher") as mock_watcher_cls:
                mock_watcher = MagicMock()
                mock_watcher_cls.return_value = mock_watcher
                fake_output = tmp_path / "result.csv"
                fake_output.write_text("a,b\n1,2\n")
                mock_watcher.wait_for_output.return_value = [fake_output]

                mock_bridge.collect.return_value = {}

                block.run(inputs={}, config=config)

            # Verify tempfile.mkdtemp was called as fallback.
            mock_mkdtemp.assert_called_once_with(prefix="scieasy_app_")


class TestFileExchangeBridgeCollection:
    """ADR-020: Collection handling in bridge.prepare()."""

    def test_prepare_handles_collection(self, tmp_path: Path) -> None:
        """Bridge should serialize Collection items into a subdirectory."""
        from scieasy.core.types.array import Image
        from scieasy.core.types.collection import Collection

        items = [
            Image(shape=(3, 3), ndim=2, dtype="uint8"),
            Image(shape=(5, 5), ndim=2, dtype="float32"),
        ]
        collection = Collection(items)

        bridge = FileExchangeBridge()
        bridge.prepare({"images": collection}, tmp_path)

        import json

        manifest = json.loads((tmp_path / "manifest.json").read_text())
        assert manifest["images"]["type"] == "collection"
        assert len(manifest["images"]["items"]) == 2
