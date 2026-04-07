"""Tests for the ``IOBlock`` abstract base class (ADR-028 §D1, T-TRK-004).

These tests verify the post-T-TRK-004 contract:

* :class:`IOBlock` cannot be instantiated directly because ``load`` and
  ``save`` are :func:`abc.abstractmethod` decorated.
* A minimal subclass that overrides both methods becomes instantiable
  and the default :meth:`IOBlock.run` correctly dispatches between
  :meth:`load` and :meth:`save` based on the ``direction`` ClassVar.
* The default ``direction='input'`` path wraps a single
  :class:`DataObject` from :meth:`load` in a single-item
  :class:`Collection` before returning it on the ``"data"`` output port.
* The ``direction='output'`` path forwards the ``"data"`` input to
  :meth:`save` and returns the configured path on the ``"path"`` key.
* Missing ``"data"`` input in output mode raises ``ValueError``.
* The class-level ``config_schema`` matches the spec body (``path``
  property only, ``path`` required).

The :class:`InMemoryIOBlock` test fixture lives in ``conftest.py`` so
that future IO tests in this directory can reuse it.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection

from .conftest import InMemoryIOBlock


class TestIOBlockIsAbstract:
    """ADR-028 §D1: ``IOBlock`` is an abstract base class."""

    def test_ioblock_cannot_be_instantiated_directly(self) -> None:
        """Calling ``IOBlock()`` must raise ``TypeError`` because ``load``
        and ``save`` are abstract."""
        with pytest.raises(TypeError, match="abstract"):
            IOBlock()  # type: ignore[abstract]

    def test_subclass_missing_overrides_is_still_abstract(self) -> None:
        """A subclass that overrides only one abstract method is still
        un-instantiable."""

        class HalfDone(IOBlock):
            def load(self, config: BlockConfig) -> DataObject | Collection:
                return DataObject()

        with pytest.raises(TypeError, match="abstract"):
            HalfDone()  # type: ignore[abstract]

    def test_load_and_save_are_abstractmethods(self) -> None:
        """Both ``load`` and ``save`` carry the ``__isabstractmethod__`` marker."""
        assert getattr(IOBlock.load, "__isabstractmethod__", False) is True
        assert getattr(IOBlock.save, "__isabstractmethod__", False) is True


class TestIOBlockConfigSchema:
    """The new spec schema (ADR-028 §D1) is intentionally minimal."""

    def test_schema_has_only_path_property(self) -> None:
        """``config_schema['properties']`` contains exactly ``path`` (the
        legacy ``direction``/``format`` fields are gone)."""
        properties = IOBlock.config_schema["properties"]
        assert set(properties.keys()) == {"path"}

    def test_path_is_required(self) -> None:
        assert IOBlock.config_schema["required"] == ["path"]

    def test_path_has_ui_priority(self) -> None:
        assert IOBlock.config_schema["properties"]["path"]["ui_priority"] == 1


class TestIOBlockSubclassDispatch:
    """The default :meth:`IOBlock.run` dispatches on ``direction``."""

    def test_input_direction_wraps_dataobject_in_collection(self) -> None:
        """``run({}, config)`` with ``direction='input'`` returns a
        single-item :class:`Collection` even when :meth:`load` returns a
        bare :class:`DataObject`."""
        block = InMemoryIOBlock(config={"params": {"path": "/tmp/in.bin"}})
        block.payload = DataObject()

        result = block.run({}, block.config)

        assert "data" in result
        coll = result["data"]
        assert isinstance(coll, Collection)
        assert coll.length == 1
        assert coll[0] is block.payload

    def test_input_direction_passes_through_existing_collection(self) -> None:
        """If :meth:`load` already returns a Collection, it must not be
        re-wrapped."""
        existing = Collection(items=[DataObject(), DataObject()], item_type=DataObject)

        class CollectionLoader(InMemoryIOBlock):
            def load(self, config: BlockConfig) -> DataObject | Collection:
                return existing

        block = CollectionLoader(config={"params": {"path": "/tmp/dir"}})
        result = block.run({}, block.config)

        assert result["data"] is existing
        assert result["data"].length == 2

    def test_output_direction_forwards_data_to_save(self) -> None:
        """``run({"data": obj}, config)`` with ``direction='output'``
        invokes :meth:`save` with the supplied object and returns the
        configured path."""

        class OutputBlock(InMemoryIOBlock):
            direction: ClassVar[str] = "output"

        block = OutputBlock(config={"params": {"path": "/tmp/out.bin"}})
        payload = DataObject()

        result = block.run({"data": payload}, block.config)

        assert block.last_saved is not None
        saved_obj, saved_config = block.last_saved
        assert saved_obj is payload
        assert saved_config is block.config
        assert result == {"path": "/tmp/out.bin"}

    def test_output_direction_missing_data_raises(self) -> None:
        """Output mode without a ``"data"`` input raises ``ValueError``."""

        class OutputBlock(InMemoryIOBlock):
            direction: ClassVar[str] = "output"

        block = OutputBlock(config={"params": {"path": "/tmp/out.bin"}})

        with pytest.raises(ValueError, match="requires 'data' input"):
            block.run({}, block.config)
