"""Tests for Block ABC — validate(), transition(), postprocess()."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.array import Array, Image
from scieasy.core.types.base import TypeSignature
from scieasy.core.types.dataframe import DataFrame

# TODO(ADR-018): Add tests for CANCELLED/SKIPPED transitions.
# TODO(ADR-019): Add test for terminate_grace_sec ClassVar.
# TODO(ADR-020): Remove tests referencing batch_mode, on_batch_error.
# TODO(ADR-020): Add tests for process_item(), pack(), unpack(), unpack_single(), map_items(), parallel_map().


class _DummyBlock(Block):
    """Minimal concrete Block subclass for testing."""

    name: ClassVar[str] = "Dummy"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Array]),
        InputPort(name="optional", accepted_types=[DataFrame], required=False),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[Array]),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"result": inputs.get("image")}


class _ConstrainedBlock(Block):
    """Block with a constraint function on its input port."""

    name: ClassVar[str] = "Constrained"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="data",
            accepted_types=[Array],
            constraint=lambda v: hasattr(v, "shape") and v.shape is not None,
            constraint_description="Must have non-None shape",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = []

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {}


class _EmptyAcceptBlock(Block):
    """Block with an input port that accepts any type."""

    name: ClassVar[str] = "EmptyAccept"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="anything", accepted_types=[]),
    ]
    output_ports: ClassVar[list[OutputPort]] = []

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {}


class TestBlockTransition:
    """Block.transition — state machine enforcement."""

    def test_idle_to_ready(self) -> None:
        block = _DummyBlock()
        assert block.state == BlockState.IDLE
        block.transition(BlockState.READY)
        assert block.state == BlockState.READY

    def test_ready_to_running(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        assert block.state == BlockState.RUNNING

    def test_running_to_done(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.DONE)
        assert block.state == BlockState.DONE

    def test_running_to_paused(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.PAUSED)
        assert block.state == BlockState.PAUSED

    def test_paused_to_running(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.PAUSED)
        block.transition(BlockState.RUNNING)
        assert block.state == BlockState.RUNNING

    def test_done_to_idle(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.DONE)
        block.transition(BlockState.IDLE)
        assert block.state == BlockState.IDLE

    def test_error_to_idle(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.ERROR)
        assert block.state == BlockState.ERROR
        block.transition(BlockState.IDLE)
        assert block.state == BlockState.IDLE

    def test_invalid_transition_raises(self) -> None:
        block = _DummyBlock()
        with pytest.raises(RuntimeError, match="Invalid state transition"):
            block.transition(BlockState.DONE)

    def test_idle_to_running_invalid(self) -> None:
        block = _DummyBlock()
        with pytest.raises(RuntimeError, match="Invalid state transition"):
            block.transition(BlockState.RUNNING)


class TestBlockValidate:
    """Block.validate — port contract checking."""

    def test_validate_correct_input(self) -> None:
        block = _DummyBlock()
        img = Image(shape=(10, 10), ndim=2, dtype="float64")
        assert block.validate({"image": img}) is True

    def test_validate_missing_required_port(self) -> None:
        block = _DummyBlock()
        with pytest.raises(ValueError, match="Required input port 'image' is missing"):
            block.validate({})

    def test_validate_optional_port_missing(self) -> None:
        block = _DummyBlock()
        img = Image(shape=(10, 10), ndim=2, dtype="float64")
        assert block.validate({"image": img}) is True

    def test_validate_wrong_type_raises(self) -> None:
        block = _DummyBlock()
        df = DataFrame(columns=["a"], row_count=1)
        with pytest.raises(ValueError, match="Port 'image'"):
            block.validate({"image": df})

    def test_validate_subtype_accepted(self) -> None:
        block = _DummyBlock()
        img = Image(shape=(10, 10), ndim=2, dtype="float64")
        assert block.validate({"image": img}) is True

    def test_validate_viewproxy_correct(self) -> None:
        """ViewProxy with compatible dtype_info passes validation."""
        from unittest.mock import MagicMock

        from scieasy.core.proxy import ViewProxy

        proxy = MagicMock(spec=ViewProxy)
        proxy.dtype_info = TypeSignature.from_type(Image)

        block = _DummyBlock()
        assert block.validate({"image": proxy}) is True

    def test_validate_viewproxy_wrong(self) -> None:
        """ViewProxy with incompatible dtype_info raises ValueError."""
        from unittest.mock import MagicMock

        from scieasy.core.proxy import ViewProxy

        proxy = MagicMock(spec=ViewProxy)
        proxy.dtype_info = TypeSignature.from_type(DataFrame)

        block = _DummyBlock()
        with pytest.raises(ValueError, match="type signature"):
            block.validate({"image": proxy})

    def test_validate_constraint_passes(self) -> None:
        block = _ConstrainedBlock()
        arr = Array(shape=(5,), ndim=1, dtype="float64")
        assert block.validate({"data": arr}) is True

    def test_validate_constraint_fails(self) -> None:
        block = _ConstrainedBlock()
        arr = Array(shape=None, ndim=1, dtype="float64")
        with pytest.raises(ValueError, match="constraint failed"):
            block.validate({"data": arr})

    def test_validate_empty_accepted_types(self) -> None:
        block = _EmptyAcceptBlock()
        assert block.validate({"anything": "literally anything"}) is True


class TestBlockPostprocess:
    """Block.postprocess — default passthrough."""

    def test_postprocess_passthrough(self) -> None:
        block = _DummyBlock()
        outputs = {"result": "value"}
        assert block.postprocess(outputs) is outputs
