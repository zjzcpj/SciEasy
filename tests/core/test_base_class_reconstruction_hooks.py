"""Tests for the six base-class reconstruction hooks (T-013).

Exercises the ``_reconstruct_extra_kwargs`` / ``_serialise_extra_metadata``
classmethod pair that T-013 adds to :class:`DataObject`,
:class:`Array`, :class:`Series`, :class:`DataFrame`, :class:`Text`,
:class:`Artifact`, and :class:`CompositeData` per ADR-027 Addendum 1
§2 ("D11' companion").

The hooks are the contract that lets :func:`_reconstruct_one` /
:func:`_serialise_one` (implemented in T-014) round-trip each base
class's constructor-specific kwargs through the JSON wire format
without a giant ``isinstance`` chain inside the worker subprocess.

T-013 ships the :mod:`scieasy.core.types.serialization` module as a
stub; its bodies raise :class:`NotImplementedError`. Tests for the
composite hook therefore verify the stub-raises behaviour rather than
round-trip — the real composite round-trip is a T-014 responsibility.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scieasy.core.types.array import Array
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject
from scieasy.core.types.composite import CompositeData
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.series import Series
from scieasy.core.types.text import Text

# ---------------------------------------------------------------------------
# DataObject base hooks (defaults return empty dict)
# ---------------------------------------------------------------------------


def test_dataobject_default_hooks_return_empty_dict() -> None:
    """The base class hook defaults are intentionally no-ops.

    Plain :class:`DataObject` only takes the four standard slots
    (``storage_ref``, ``framework``, ``meta``, ``user``) and therefore
    has no extras to round-trip. Concrete base classes override.
    """
    assert DataObject._reconstruct_extra_kwargs({}) == {}
    assert DataObject._reconstruct_extra_kwargs({"junk": 1}) == {}

    obj = DataObject()
    assert DataObject._serialise_extra_metadata(obj) == {}


def test_dataobject_hooks_are_classmethods() -> None:
    """Both hooks are classmethods and can be called off the type itself."""
    import inspect

    # classmethod objects expose __self__ == the class after binding.
    cls_kwargs_fn = DataObject.__dict__["_reconstruct_extra_kwargs"]
    cls_md_fn = DataObject.__dict__["_serialise_extra_metadata"]
    assert isinstance(cls_kwargs_fn, classmethod)
    assert isinstance(cls_md_fn, classmethod)
    # And calling them on the class works without an instance.
    assert inspect.signature(DataObject._reconstruct_extra_kwargs).parameters
    assert inspect.signature(DataObject._serialise_extra_metadata).parameters


# ---------------------------------------------------------------------------
# Array hooks
# ---------------------------------------------------------------------------


def test_array_reconstruct_extra_kwargs_returns_correct_fields() -> None:
    """Array extracts axes/shape/dtype/chunk_shape and tuplifies shape fields."""
    metadata = {
        "axes": ["t", "z", "y", "x"],
        "shape": [10, 20, 64, 64],
        "dtype": "uint16",
        "chunk_shape": [1, 1, 64, 64],
    }
    kwargs = Array._reconstruct_extra_kwargs(metadata)

    assert kwargs == {
        "axes": ["t", "z", "y", "x"],
        "shape": (10, 20, 64, 64),
        "dtype": "uint16",
        "chunk_shape": (1, 1, 64, 64),
    }
    # Shape and chunk_shape must be tuples, not lists.
    assert isinstance(kwargs["shape"], tuple)
    assert isinstance(kwargs["chunk_shape"], tuple)


def test_array_reconstruct_extra_kwargs_handles_metadata_only() -> None:
    """Array with no shape / chunk_shape round-trips as None, not empty tuple."""
    metadata = {"axes": ["y", "x"], "dtype": None}
    kwargs = Array._reconstruct_extra_kwargs(metadata)
    assert kwargs["axes"] == ["y", "x"]
    assert kwargs["shape"] is None
    assert kwargs["dtype"] is None
    assert kwargs["chunk_shape"] is None


def test_array_serialise_extra_metadata_returns_correct_fields() -> None:
    """Array emits JSON-clean lists for shape fields and a stringified dtype."""
    arr = Array(
        axes=["y", "x"],
        shape=(32, 48),
        dtype="float32",
        chunk_shape=(32, 48),
    )
    md = Array._serialise_extra_metadata(arr)
    assert md == {
        "axes": ["y", "x"],
        "shape": [32, 48],
        "dtype": "float32",
        "chunk_shape": [32, 48],
    }
    assert isinstance(md["shape"], list)
    assert isinstance(md["chunk_shape"], list)
    assert isinstance(md["dtype"], str)


def test_array_round_trip_via_hooks() -> None:
    """Serialise then reconstruct an Array via the hook pair; verify equality."""
    original = Array(
        axes=["t", "z", "c", "y", "x"],
        shape=(5, 10, 3, 256, 256),
        dtype="uint8",
        chunk_shape=(1, 1, 1, 256, 256),
    )
    md = Array._serialise_extra_metadata(original)
    kwargs = Array._reconstruct_extra_kwargs(md)
    reconstructed = Array(**kwargs)

    assert reconstructed.axes == original.axes
    assert reconstructed.shape == original.shape
    assert reconstructed.dtype == original.dtype
    assert reconstructed.chunk_shape == original.chunk_shape


def test_array_round_trip_metadata_only_none_fields() -> None:
    """Metadata-only Array (shape=None, chunk_shape=None) round-trips cleanly."""
    original = Array(axes=["y", "x"])
    md = Array._serialise_extra_metadata(original)
    kwargs = Array._reconstruct_extra_kwargs(md)
    reconstructed = Array(**kwargs)

    assert reconstructed.axes == ["y", "x"]
    assert reconstructed.shape is None
    assert reconstructed.dtype is None
    assert reconstructed.chunk_shape is None


# ---------------------------------------------------------------------------
# Series hooks
# ---------------------------------------------------------------------------


def test_series_reconstruct_extra_kwargs_returns_correct_fields() -> None:
    metadata = {
        "index_name": "wavenumber",
        "value_name": "intensity",
        "length": 2048,
    }
    assert Series._reconstruct_extra_kwargs(metadata) == metadata


def test_series_serialise_extra_metadata_returns_correct_fields() -> None:
    series = Series(index_name="time", value_name="voltage", length=1000)
    md = Series._serialise_extra_metadata(series)
    assert md == {
        "index_name": "time",
        "value_name": "voltage",
        "length": 1000,
    }


def test_series_round_trip_via_hooks() -> None:
    original = Series(index_name="mz", value_name="intensity", length=4096)
    md = Series._serialise_extra_metadata(original)
    kwargs = Series._reconstruct_extra_kwargs(md)
    reconstructed = Series(**kwargs)

    assert reconstructed.index_name == original.index_name
    assert reconstructed.value_name == original.value_name
    assert reconstructed.length == original.length


def test_series_round_trip_with_missing_fields() -> None:
    """Missing optional fields round-trip as ``None``."""
    md: dict = {}
    kwargs = Series._reconstruct_extra_kwargs(md)
    reconstructed = Series(**kwargs)
    assert reconstructed.index_name is None
    assert reconstructed.value_name is None
    assert reconstructed.length is None


# ---------------------------------------------------------------------------
# DataFrame hooks
# ---------------------------------------------------------------------------


def test_dataframe_reconstruct_extra_kwargs_returns_correct_fields() -> None:
    metadata = {
        "columns": ["a", "b", "c"],
        "row_count": 42,
        "schema": {"a": "int64", "b": "float64", "c": "string"},
    }
    kwargs = DataFrame._reconstruct_extra_kwargs(metadata)
    assert kwargs == {
        "columns": ["a", "b", "c"],
        "row_count": 42,
        "schema": {"a": "int64", "b": "float64", "c": "string"},
    }


def test_dataframe_serialise_extra_metadata_returns_correct_fields() -> None:
    df = DataFrame(columns=["x", "y"], row_count=100, schema={"x": "int", "y": "float"})
    md = DataFrame._serialise_extra_metadata(df)
    assert md == {
        "columns": ["x", "y"],
        "row_count": 100,
        "schema": {"x": "int", "y": "float"},
    }


def test_dataframe_round_trip_via_hooks() -> None:
    original = DataFrame(
        columns=["peak_mz", "peak_intensity", "retention_time"],
        row_count=5000,
        schema={"peak_mz": "float64", "peak_intensity": "float64", "retention_time": "float64"},
    )
    md = DataFrame._serialise_extra_metadata(original)
    kwargs = DataFrame._reconstruct_extra_kwargs(md)
    reconstructed = DataFrame(**kwargs)

    assert reconstructed.columns == original.columns
    assert reconstructed.row_count == original.row_count
    assert reconstructed.schema == original.schema


def test_dataframe_round_trip_empty_defaults() -> None:
    """A DataFrame reconstructed from an empty metadata dict has empty column/schema."""
    kwargs = DataFrame._reconstruct_extra_kwargs({})
    reconstructed = DataFrame(**kwargs)
    assert reconstructed.columns == []
    assert reconstructed.row_count is None
    assert reconstructed.schema == {}


# ---------------------------------------------------------------------------
# Text hooks
# ---------------------------------------------------------------------------


def test_text_reconstruct_extra_kwargs_returns_correct_fields() -> None:
    metadata = {"content": "hello", "format": "markdown", "encoding": "utf-16"}
    kwargs = Text._reconstruct_extra_kwargs(metadata)
    assert kwargs == {
        "content": "hello",
        "format": "markdown",
        "encoding": "utf-16",
    }


def test_text_reconstruct_extra_kwargs_applies_defaults() -> None:
    """Missing format/encoding fall back to the constructor defaults."""
    kwargs = Text._reconstruct_extra_kwargs({})
    assert kwargs == {"content": None, "format": "plain", "encoding": "utf-8"}


def test_text_serialise_extra_metadata_returns_correct_fields() -> None:
    text = Text(content="ABC", format="plain", encoding="utf-8")
    md = Text._serialise_extra_metadata(text)
    assert md == {"content": "ABC", "format": "plain", "encoding": "utf-8"}


def test_text_round_trip_via_hooks() -> None:
    original = Text(content="# Heading\n\nbody", format="markdown", encoding="utf-8")
    md = Text._serialise_extra_metadata(original)
    kwargs = Text._reconstruct_extra_kwargs(md)
    reconstructed = Text(**kwargs)

    assert reconstructed.content == original.content
    assert reconstructed.format == original.format
    assert reconstructed.encoding == original.encoding


# ---------------------------------------------------------------------------
# Artifact hooks
# ---------------------------------------------------------------------------


def test_artifact_reconstruct_extra_kwargs_returns_correct_fields() -> None:
    metadata = {
        "file_path": "/tmp/report.pdf",
        "mime_type": "application/pdf",
        "description": "Quarterly report",
    }
    kwargs = Artifact._reconstruct_extra_kwargs(metadata)
    assert kwargs["file_path"] == Path("/tmp/report.pdf")
    assert isinstance(kwargs["file_path"], Path)
    assert kwargs["mime_type"] == "application/pdf"
    assert kwargs["description"] == "Quarterly report"


def test_artifact_reconstruct_extra_kwargs_handles_none_path() -> None:
    """A missing file_path round-trips as ``None``, not ``Path('.')``."""
    kwargs = Artifact._reconstruct_extra_kwargs({})
    assert kwargs["file_path"] is None
    assert kwargs["mime_type"] is None
    assert kwargs["description"] == ""


def test_artifact_serialise_extra_metadata_returns_correct_fields() -> None:
    artifact = Artifact(
        file_path=Path("/tmp/output.bin"),
        mime_type="application/octet-stream",
        description="binary dump",
    )
    md = Artifact._serialise_extra_metadata(artifact)
    # file_path must be stringified (JSON-clean).
    assert md["file_path"] == str(Path("/tmp/output.bin"))
    assert isinstance(md["file_path"], str)
    assert md["mime_type"] == "application/octet-stream"
    assert md["description"] == "binary dump"


def test_artifact_round_trip_via_hooks() -> None:
    original = Artifact(
        file_path=Path("/data/figure.png"),
        mime_type="image/png",
        description="test figure",
    )
    md = Artifact._serialise_extra_metadata(original)
    # Verify the wire format is JSON-clean (no Path objects).
    import json

    json.dumps(md)  # must not raise

    kwargs = Artifact._reconstruct_extra_kwargs(md)
    reconstructed = Artifact(**kwargs)

    assert reconstructed.file_path == original.file_path
    assert reconstructed.mime_type == original.mime_type
    assert reconstructed.description == original.description


def test_artifact_round_trip_none_path() -> None:
    """Artifact with file_path=None round-trips cleanly."""
    original = Artifact(file_path=None, mime_type="text/plain", description="")
    md = Artifact._serialise_extra_metadata(original)
    assert md["file_path"] is None
    kwargs = Artifact._reconstruct_extra_kwargs(md)
    reconstructed = Artifact(**kwargs)
    assert reconstructed.file_path is None


# ---------------------------------------------------------------------------
# CompositeData hooks (T-013: verify the lazy-import wiring reaches the stub)
# ---------------------------------------------------------------------------


def test_composite_reconstruct_raises_until_t014() -> None:
    """Composite reconstruction delegates to the T-013 stub, which raises.

    T-014 replaces the :func:`_reconstruct_one` stub body with the real
    implementation. Until then, attempting to reconstruct a composite
    with at least one slot should surface the ``NotImplementedError``
    with a pointer back to T-014.
    """
    metadata = {"slots": {"image": {"backend": "zarr", "path": "/tmp/x", "metadata": {}}}}
    with pytest.raises(NotImplementedError, match="T-014"):
        CompositeData._reconstruct_extra_kwargs(metadata)


def test_composite_reconstruct_empty_slots_does_not_call_stub() -> None:
    """No slots ⇒ no delegation ⇒ no NotImplementedError.

    The hook only calls :func:`_reconstruct_one` per slot; an empty
    ``slots`` dict short-circuits to ``{"slots": {}}`` without hitting
    the stub. This lets T-013 ship without breaking plugin tests that
    construct an empty composite.
    """
    kwargs = CompositeData._reconstruct_extra_kwargs({"slots": {}})
    assert kwargs == {"slots": {}}

    # And a missing ``slots`` key also short-circuits.
    kwargs2 = CompositeData._reconstruct_extra_kwargs({})
    assert kwargs2 == {"slots": {}}


def test_composite_serialise_raises_until_t014() -> None:
    """Composite serialisation with at least one slot raises via the stub."""
    inner = Array(axes=["y", "x"], shape=(4, 4), dtype="uint8")
    composite = CompositeData(slots={"img": inner})
    with pytest.raises(NotImplementedError, match="T-014"):
        CompositeData._serialise_extra_metadata(composite)


def test_composite_serialise_empty_slots_does_not_call_stub() -> None:
    """An empty composite serialises to ``{"slots": {}}`` without delegation."""
    empty = CompositeData()
    md = CompositeData._serialise_extra_metadata(empty)
    assert md == {"slots": {}}


# ---------------------------------------------------------------------------
# serialization stub module
# ---------------------------------------------------------------------------


def test_serialization_module_imports() -> None:
    """The stub module must be importable and expose both helpers.

    T-014 will replace the bodies but must keep the signatures. This
    test locks the public surface.
    """
    from scieasy.core.types import serialization
    from scieasy.core.types.serialization import _reconstruct_one, _serialise_one

    assert callable(_reconstruct_one)
    assert callable(_serialise_one)
    assert hasattr(serialization, "_reconstruct_one")
    assert hasattr(serialization, "_serialise_one")


def test_serialization_stub_reconstruct_raises() -> None:
    """The stub's ``_reconstruct_one`` must raise :class:`NotImplementedError`."""
    from scieasy.core.types.serialization import _reconstruct_one

    with pytest.raises(NotImplementedError, match="T-014"):
        _reconstruct_one({"backend": "zarr", "path": "/x", "metadata": {}})


def test_serialization_stub_serialise_raises() -> None:
    """The stub's ``_serialise_one`` must raise :class:`NotImplementedError`."""
    from scieasy.core.types.serialization import _serialise_one

    with pytest.raises(NotImplementedError, match="T-014"):
        _serialise_one(DataObject())


# ---------------------------------------------------------------------------
# Cross-class discovery: all six base classes declare both hooks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base_class",
    [DataObject, Array, Series, DataFrame, Text, Artifact, CompositeData],
)
def test_all_six_base_classes_have_both_hooks(base_class: type) -> None:
    """Every core base class must declare both hook classmethods.

    This is the contract T-014's worker relies on: it calls
    ``cls._reconstruct_extra_kwargs(md)`` and
    ``type(obj)._serialise_extra_metadata(obj)`` unconditionally,
    trusting that every registered type provides them (inherited from
    the :class:`DataObject` default if not overridden).
    """
    assert hasattr(base_class, "_reconstruct_extra_kwargs")
    assert hasattr(base_class, "_serialise_extra_metadata")
    # Must be classmethods (callable off the class directly).
    assert callable(base_class._reconstruct_extra_kwargs)
    assert callable(base_class._serialise_extra_metadata)
    # Default behaviour on an empty metadata dict must not raise
    # (except for CompositeData, whose empty-slots short-circuit is
    # already verified above — but even there, {} should be safe).
    result = base_class._reconstruct_extra_kwargs({})
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Plugin-subclass override pattern (documented in ADR-027 Addendum 1 §2)
# ---------------------------------------------------------------------------


class _PluginArray(Array):
    """Hypothetical plugin subclass that adds an extra geometry field."""

    @classmethod
    def _reconstruct_extra_kwargs(cls, metadata: dict) -> dict:
        kwargs = super()._reconstruct_extra_kwargs(metadata)
        kwargs["_plugin_extra"] = metadata.get("plugin_extra", "default")
        return kwargs

    @classmethod
    def _serialise_extra_metadata(cls, obj: _PluginArray) -> dict:
        md = super()._serialise_extra_metadata(obj)
        md["plugin_extra"] = getattr(obj, "_plugin_extra", "default")
        return md


def test_plugin_subclass_can_override_and_super() -> None:
    """Plugin subclasses chain via ``super()`` to pick up parent extras.

    ADR-027 Addendum 1 §2 documents this as the override pattern:
    plugin subclasses that add geometry-like fields outside the ``Meta``
    Pydantic model override ``_reconstruct_extra_kwargs`` and call
    ``super()._reconstruct_extra_kwargs(metadata)`` to inherit the
    parent class's extras, then extend the returned dict.
    """
    metadata = {
        "axes": ["y", "x"],
        "shape": [8, 8],
        "dtype": "uint8",
        "chunk_shape": None,
        "plugin_extra": "hyperspectral",
    }
    kwargs = _PluginArray._reconstruct_extra_kwargs(metadata)
    # Parent-class extras are present.
    assert kwargs["axes"] == ["y", "x"]
    assert kwargs["shape"] == (8, 8)
    assert kwargs["dtype"] == "uint8"
    assert kwargs["chunk_shape"] is None
    # Plugin extra is added on top.
    assert kwargs["_plugin_extra"] == "hyperspectral"
