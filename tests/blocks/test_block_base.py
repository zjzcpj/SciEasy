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


class TestBlockTransitionCancelledSkipped:
    """ADR-018: CANCELLED and SKIPPED state transitions."""

    def test_running_to_cancelled(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.CANCELLED)
        assert block.state == BlockState.CANCELLED

    def test_paused_to_cancelled(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.PAUSED)
        block.transition(BlockState.CANCELLED)
        assert block.state == BlockState.CANCELLED

    def test_idle_to_skipped(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.SKIPPED)
        assert block.state == BlockState.SKIPPED

    def test_ready_to_skipped(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.SKIPPED)
        assert block.state == BlockState.SKIPPED

    def test_cancelled_to_idle(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.CANCELLED)
        block.transition(BlockState.IDLE)
        assert block.state == BlockState.IDLE

    def test_skipped_to_idle(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.SKIPPED)
        block.transition(BlockState.IDLE)
        assert block.state == BlockState.IDLE

    def test_done_to_cancelled_invalid(self) -> None:
        block = _DummyBlock()
        block.transition(BlockState.READY)
        block.transition(BlockState.RUNNING)
        block.transition(BlockState.DONE)
        with pytest.raises(RuntimeError, match="Invalid state transition"):
            block.transition(BlockState.CANCELLED)

    def test_idle_to_cancelled_invalid(self) -> None:
        block = _DummyBlock()
        with pytest.raises(RuntimeError, match="Invalid state transition"):
            block.transition(BlockState.CANCELLED)


class TestTerminateGraceSec:
    """ADR-019: terminate_grace_sec ClassVar."""

    def test_default_value(self) -> None:
        block = _DummyBlock()
        assert block.terminate_grace_sec == 5.0

    def test_custom_subclass(self) -> None:
        class CustomBlock(Block):
            name: ClassVar[str] = "Custom"
            terminate_grace_sec: ClassVar[float] = 10.0

            def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
                return {}

        block = CustomBlock()
        assert block.terminate_grace_sec == 10.0


class TestValidateCollectionTransparency:
    """Issue #129: Block.validate() correctly validates Collection inputs via item_type."""

    def test_validate_collection_with_matching_item_type(self) -> None:
        """Collection[Image] should pass validation for a port accepting Array."""
        from scieasy.core.types.collection import Collection

        block = _DummyBlock()
        img = Image(shape=(10, 10), ndim=2, dtype="float64")
        c = Collection([img])
        # Collection[Image] -> port accepts Array -> Image is subtype of Array -> pass
        assert block.validate({"image": c}) is True

    def test_validate_collection_with_wrong_item_type(self) -> None:
        """Collection[DataFrame] should fail validation for a port accepting Array."""
        from scieasy.core.types.collection import Collection

        block = _DummyBlock()
        df = DataFrame(columns=["a"], row_count=1)
        c = Collection([df])
        with pytest.raises(ValueError, match="Collection item type"):
            block.validate({"image": c})

    def test_validate_collection_exact_item_type(self) -> None:
        """Collection[Image] should pass validation for a port accepting Image."""
        from scieasy.core.types.collection import Collection

        class _ImageBlock(Block):
            name: ClassVar[str] = "ImageOnly"
            input_ports: ClassVar[list[InputPort]] = [
                InputPort(name="img", accepted_types=[Image]),
            ]
            output_ports: ClassVar[list[OutputPort]] = []

            def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
                return {}

        block = _ImageBlock()
        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img])
        assert block.validate({"img": c}) is True

    def test_validate_collection_empty_accepted_types(self) -> None:
        """Collection should pass validation for a port accepting anything."""
        from scieasy.core.types.collection import Collection

        block = _EmptyAcceptBlock()
        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img])
        assert block.validate({"anything": c}) is True


class TestCollectionUtilities:
    """ADR-020: pack(), unpack(), unpack_single(), map_items(), parallel_map()."""

    def test_pack_creates_collection(self) -> None:
        from scieasy.core.types.collection import Collection

        items = [Image(shape=(10, 10), ndim=2, dtype="float64")]
        result = Block.pack(items, item_type=Image)
        assert isinstance(result, Collection)
        assert result.length == 1
        assert result.item_type is Image

    def test_unpack_returns_list(self) -> None:
        from scieasy.core.types.collection import Collection

        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img], item_type=Image)
        items = Block.unpack(c)
        assert isinstance(items, list)
        assert len(items) == 1
        assert items[0] is img

    def test_unpack_single(self) -> None:
        from scieasy.core.types.collection import Collection

        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img])
        result = Block.unpack_single(c)
        assert result is img

    def test_unpack_single_multi_raises(self) -> None:
        from scieasy.core.types.collection import Collection

        items = [
            Image(shape=(5, 5), ndim=2, dtype="uint8"),
            Image(shape=(3, 3), ndim=2, dtype="uint8"),
        ]
        c = Collection(items)
        with pytest.raises(ValueError, match="single-item"):
            Block.unpack_single(c)

    def test_map_items(self) -> None:
        from scieasy.core.types.collection import Collection

        items = [
            Image(shape=(5, 5), ndim=2, dtype="uint8"),
            Image(shape=(3, 3), ndim=2, dtype="float32"),
        ]
        c = Collection(items)
        result = Block.map_items(lambda x: x, c)
        assert isinstance(result, Collection)
        assert result.length == 2


class TestAutoFlush:
    """Block._auto_flush — auto-persistence of in-memory DataObjects."""

    def teardown_method(self) -> None:
        """Clear flush context after each test."""
        from scieasy.core.storage.flush_context import clear

        clear()

    def test_auto_flush_non_dataobject(self) -> None:
        """Non-DataObject values pass through unchanged."""
        result = Block._auto_flush("just a string")
        assert result == "just a string"

    def test_auto_flush_already_has_ref(self) -> None:
        """DataObject with an existing StorageReference passes through."""
        from scieasy.core.storage.ref import StorageReference

        img = Image(shape=(5, 5), ndim=2, dtype="float64")
        img.storage_ref = StorageReference(backend="zarr", path="/tmp/test.zarr")
        result = Block._auto_flush(img)
        assert result is img

    def test_auto_flush_no_context(self) -> None:
        """Without flush context, in-memory DataObject returns unchanged."""
        from scieasy.core.storage.flush_context import clear

        clear()
        img = Image(shape=(5, 5), ndim=2, dtype="float64")
        result = Block._auto_flush(img)
        assert result is img
        assert result.storage_ref is None

    def test_auto_flush_with_context_persists(self, tmp_path: object) -> None:
        """With flush context set, _auto_flush writes data and sets storage_ref."""
        import numpy as np

        from scieasy.core.storage.flush_context import set_output_dir

        output_dir = str(tmp_path)
        set_output_dir(output_dir)

        img = Image(shape=(3, 3), ndim=2, dtype="float64")
        img._data = np.ones((3, 3), dtype="float64")

        result = Block._auto_flush(img)
        assert result is img
        assert result.storage_ref is not None
        assert result.storage_ref.backend == "zarr"
