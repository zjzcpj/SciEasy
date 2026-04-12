"""IOBlock example: load .npy files with streaming persistence.

This block demonstrates the IOBlock pattern with persist_array() for
constant-memory loading. For small files, the simple path (return
in-memory, let auto-flush handle it) also works.

Usage:
    Include in a Tier 2 package with scieasy.blocks entry-point.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.meta.framework import FrameworkMeta
from scieasy.core.types.array import Array
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection


class LoadNpy(IOBlock):
    """Load a .npy file into an Array data object.

    Demonstrates two loading paths:

    1. **Simple path** (small files): Load into memory, return Array.
       The base class auto-flushes to zarr storage (ADR-031 D4 safety net).
    2. **Streaming path** (large files): Use memory-mapped read +
       ``persist_array()`` with chunk iteration to write to zarr with
       constant memory. Returns a reference-only Array.
    """

    direction: ClassVar[str] = "input"
    name: ClassVar[str] = "Load NPY"
    description: ClassVar[str] = "Load a NumPy .npy file into an Array."
    subcategory: ClassVar[str] = "io"

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="array", accepted_types=[Array]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "axes": {
                "type": "string",
                "title": "Axis labels (e.g., 'cyx')",
                "ui_priority": 1,
            },
            "streaming": {
                "type": "boolean",
                "default": False,
                "title": "Use streaming persistence (for large files)",
                "ui_priority": 2,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig, output_dir: str = "") -> DataObject | Collection:
        """Load the .npy file.

        Args:
            config: BlockConfig with ``path``, optional ``axes`` and
                ``streaming`` fields.
            output_dir: Directory for zarr persistence (ADR-031 D4).

        Returns:
            A single-item Collection containing the loaded Array.
        """
        raw_path = config.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError("LoadNpy: config['path'] must be a non-empty string")

        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"LoadNpy: no file at {path}")
        if path.suffix.lower() != ".npy":
            raise ValueError(f"LoadNpy: expected .npy file, got {path.suffix}")

        streaming = bool(config.get("streaming", False))

        if streaming and output_dir:
            return self._load_streaming(path, config, output_dir)
        return self._load_simple(path, config)

    def _load_simple(self, path: Path, config: BlockConfig) -> Array:
        """Simple path: load into memory, let auto-flush handle persistence.

        Suitable for small files (< 1 GB). The returned Array has no
        storage_ref; the IOBlock base class auto-flushes it to zarr
        before it crosses the block boundary (ADR-031 D4 safety net).
        """
        data = np.load(str(path))
        axes = self._resolve_axes(config, data.ndim)

        # Return in-memory Array — base class handles persistence.
        # Do NOT set _data directly; pass data through the constructor
        # or let auto-flush write it from get_in_memory_data().
        arr = Array(
            axes=axes,
            shape=tuple(data.shape),
            dtype=str(data.dtype),
            framework=FrameworkMeta(source=str(path)),
        )
        # Attach data for auto-flush to persist (transient, within block only).
        arr._data = data  # type: ignore[attr-defined]
        return arr

    def _load_streaming(self, path: Path, config: BlockConfig, output_dir: str) -> Array:
        """Streaming path: memory-mapped read + chunked zarr write.

        Uses np.load(mmap_mode='r') so the file is NOT fully loaded into
        memory. Then iterates chunks and yields them to persist_array()
        for constant-memory zarr writes. Suitable for large files (> 1 GB).
        """
        # Memory-mapped read — does NOT load data into RAM
        mmap = np.load(str(path), mmap_mode="r")
        axes = self._resolve_axes(config, mmap.ndim)
        shape = tuple(mmap.shape)
        dtype = mmap.dtype

        if mmap.ndim >= 2:
            # Stream first-axis slices (e.g., z-planes for a 3D array)
            def chunk_iter():
                for i in range(shape[0]):
                    yield (i, np.asarray(mmap[i]))

            ref = self.persist_array(chunk_iter(), shape, dtype, output_dir)
        else:
            # 1D array: single chunk, use ndarray mode
            ref = self.persist_array(np.asarray(mmap), shape, dtype, output_dir)

        return Array(
            axes=axes,
            shape=shape,
            dtype=str(dtype),
            framework=FrameworkMeta(source=str(path)),
            storage_ref=ref,
        )

    @staticmethod
    def _resolve_axes(config: BlockConfig, ndim: int) -> list[str]:
        """Resolve axis labels from config or defaults."""
        axes_str = config.get("axes")
        if axes_str and isinstance(axes_str, str):
            axes = list(axes_str)
            if len(axes) != ndim:
                raise ValueError(f"LoadNpy: axes '{axes_str}' length {len(axes)} != ndim {ndim}")
            return axes
        # Default axis naming
        defaults = {2: ["y", "x"], 3: ["c", "y", "x"], 4: ["t", "c", "y", "x"]}
        if ndim in defaults:
            return defaults[ndim]
        return [f"dim{i}" for i in range(ndim)]

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Not supported -- LoadNpy is an input block."""
        raise NotImplementedError("LoadNpy is an input block; use direction='output' blocks to save.")
