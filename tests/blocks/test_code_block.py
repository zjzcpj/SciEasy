"""Tests for CodeBlock — inline Python, script Python, PROXY mode, CHUNKED mode."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.blocks.code.code_block import CodeBlock
from scieasy.blocks.code.introspect import introspect_script
from scieasy.blocks.code.runners.python_runner import PythonRunner
from scieasy.core.proxy import ViewProxy

# TODO(ADR-020-Add4): Add tests for Collection auto-unpack/repack:
#   single item -> native object, multiple items -> LazyList, list output -> Collection.


@pytest.mark.skip(reason="ADR-017: PythonRunner rewritten to use subprocess. Tests need update.")
class TestPythonRunnerInline:
    """PythonRunner inline mode — exec() in namespace."""

    def test_simple_script(self) -> None:
        runner = PythonRunner()
        result = runner.execute_inline("x = 2\ny = x * 3", {})
        assert result["x"] == 2
        assert result["y"] == 6

    def test_script_with_inputs(self) -> None:
        runner = PythonRunner()
        result = runner.execute_inline("out = data + 10", {"data": 5})
        assert result["out"] == 15

    def test_private_keys_stripped(self) -> None:
        runner = PythonRunner()
        result = runner.execute_inline("_private = 1\npublic = 2", {})
        assert "public" in result
        assert "_private" not in result


@pytest.mark.skip(reason="ADR-017: PythonRunner rewritten to use subprocess. Tests need update.")
class TestPythonRunnerScript:
    """PythonRunner script mode — importlib-based execution."""

    def test_script_file(self, tmp_path: Path) -> None:
        script = tmp_path / "my_block.py"
        script.write_text("def run(inputs, config):\n    return {'result': inputs['value'] * 2}\n")
        runner = PythonRunner()
        result = runner.execute_script(script, "run", {"value": 21}, {})
        assert result["result"] == 42

    def test_missing_script(self) -> None:
        runner = PythonRunner()
        with pytest.raises(FileNotFoundError):
            runner.execute_script("/nonexistent.py", "run", {}, {})

    def test_missing_function(self, tmp_path: Path) -> None:
        script = tmp_path / "empty.py"
        script.write_text("# no run function\n")
        runner = PythonRunner()
        with pytest.raises(AttributeError, match="run"):
            runner.execute_script(script, "run", {}, {})


@pytest.mark.skip(reason="ADR-017: CodeBlock rewritten to use subprocess. Tests need update.")
class TestCodeBlockInline:
    """CodeBlock inline mode with MEMORY delivery."""

    def test_inline_execution(self) -> None:
        block = CodeBlock(config={"params": {"script": "result = 42", "delivery": "memory"}})
        block.transition(BlockState.READY)
        result = block.run({}, block.config)
        assert result["result"] == 42

    def test_inline_with_input(self) -> None:
        block = CodeBlock(config={"params": {"script": "output = data * 2", "delivery": "memory"}})
        block.transition(BlockState.READY)
        result = block.run({"data": 10}, block.config)
        assert result["output"] == 20


@pytest.mark.skip(reason="ADR-017: CodeBlock rewritten to use subprocess. Tests need update.")
class TestCodeBlockScript:
    """CodeBlock script mode."""

    def test_script_execution(self, tmp_path: Path) -> None:
        script = tmp_path / "block_script.py"
        script.write_text("def run(inputs, config):\n    return {'result': sum(inputs.get('values', []))}\n")
        block = CodeBlock(config={"params": {"script_path": str(script), "delivery": "memory"}})
        block.mode = "script"
        block.transition(BlockState.READY)
        result = block.run({"values": [1, 2, 3]}, block.config)
        assert result["result"] == 6


@pytest.mark.skip(reason="ADR-017: CodeBlock rewritten to use subprocess. Tests need update.")
class TestCodeBlockProxyMode:
    """CodeBlock PROXY delivery — passes ViewProxy directly."""

    def test_proxy_passthrough(self) -> None:
        """Verify that PROXY mode passes the ViewProxy without materialising."""
        block = CodeBlock(config={"params": {"script": "result = type(data).__name__", "delivery": "proxy"}})
        block.transition(BlockState.READY)

        # Create a mock ViewProxy.
        proxy = MagicMock(spec=ViewProxy)
        proxy.to_memory = MagicMock(return_value="should not be called")

        result = block.run({"data": proxy}, block.config)
        assert result["result"] == "MagicMock"
        # to_memory should NOT have been called.
        proxy.to_memory.assert_not_called()


@pytest.mark.skip(reason="ADR-017: CodeBlock rewritten to use subprocess. Tests need update.")
class TestCodeBlockChunkedMode:
    """CodeBlock CHUNKED delivery — iterates chunks."""

    def test_chunked_delivery(self) -> None:
        """Verify CHUNKED mode calls iter_chunks and delivers a list."""
        block = CodeBlock(config={"params": {"script": "result = len(data)", "delivery": "chunked", "chunk_size": 2}})
        block.transition(BlockState.READY)

        proxy = MagicMock(spec=ViewProxy)
        proxy.iter_chunks = MagicMock(return_value=iter([np.array([1, 2]), np.array([3, 4])]))

        result = block.run({"data": proxy}, block.config)
        # The input 'data' should be a list of chunks.
        assert result["result"] == 2
        proxy.iter_chunks.assert_called_once_with(2)


class TestIntrospectScript:
    """introspect_script — AST-based script analysis."""

    def test_simple_run_function(self, tmp_path: Path) -> None:
        script = tmp_path / "block.py"
        script.write_text('"""My block."""\ndef run(inputs, config, threshold=0.5):\n    pass\n')
        info = introspect_script(script)
        assert info["has_run"] is True
        assert len(info["run_params"]) == 3
        assert info["run_params"][0]["name"] == "inputs"
        assert info["docstring"] == "My block."

    def test_configure_function(self, tmp_path: Path) -> None:
        script = tmp_path / "block.py"
        script.write_text(
            "def configure():\n    return {'window': 11, 'method': 'savgol'}\n\ndef run(inputs, config):\n    pass\n"
        )
        info = introspect_script(script)
        assert info["has_configure"] is True
        assert info["configure_schema"] == {"window": 11, "method": "savgol"}

    def test_no_run_function(self, tmp_path: Path) -> None:
        script = tmp_path / "utils.py"
        script.write_text("x = 1\n")
        info = introspect_script(script)
        assert info["has_run"] is False

    def test_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            introspect_script("/nonexistent.py")
