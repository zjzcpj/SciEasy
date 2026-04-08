"""CellposeSegment — flagship deep-learning cell segmentation (T-IMG-019).

FLAGSHIP block for Phase 11 imaging. Demonstrates the ADR-027 D7
``setup`` / ``teardown`` lifecycle: the cellpose model is loaded
ONCE per :meth:`run` (in :meth:`setup`), reused across every
``process_item`` call via the shared ``state`` object, and freed in
:meth:`teardown` (which also calls ``torch.cuda.empty_cache()`` when
torch+CUDA are present).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-019.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image, Label


class CellposeSegment(ProcessBlock):
    """Flagship segmentation block using cellpose deep learning models.

    Implements ADR-027 D7 ``setup`` / ``teardown`` to load the cellpose
    model ONCE per run, not per item. The model lives in the ``state``
    object passed through to :meth:`process_item`.

    Per Q-IMG-2: defaults to CPU. Set ``use_gpu=True`` to use CUDA when
    available; cellpose falls back to CPU automatically when CUDA is
    not present.

    Optional dependency. Install with::

        pip install scieasy-blocks-imaging[cellpose]
    """

    type_name: ClassVar[str] = "imaging.cellpose_segment"
    name: ClassVar[str] = "Cellpose Segmentation"
    description: ClassVar[str] = (
        "Cellpose deep-learning cell segmentation (FLAGSHIP). "
        "Loads the cellpose model once per run via setup()/teardown()."
    )
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "cellpose"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="images", accepted_types=[Collection[Image]], required=True),  # type: ignore[misc]
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="labels", accepted_types=[Collection[Label]]),  # type: ignore[misc]
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "enum": ["cyto3", "cyto2", "nuclei", "custom"],
                "default": "cyto3",
            },
            "diameter": {"type": "number", "default": 30.0, "minimum": 0.0},
            "flow_threshold": {
                "type": "number",
                "default": 0.4,
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "cellprob_threshold": {"type": "number", "default": 0.0},
            "use_gpu": {"type": "boolean", "default": False},
            "channels": {"type": "array", "default": [0, 0]},
            "custom_model_path": {"type": "string"},
        },
    }

    def setup(self, config: BlockConfig) -> Any:
        """Load the cellpose model ONCE per :meth:`run` (ADR-027 D7).

        Returns:
            The loaded cellpose model object. This becomes the
            ``state`` argument to :meth:`process_item`.

        Raises:
            ImportError: If the optional ``cellpose`` package is not
                installed (friendly error pointing at the ``[cellpose]``
                extra).
            ValueError: If ``model="custom"`` is set without
                ``custom_model_path``.
        """
        raise NotImplementedError(
            "T-IMG-019 CellposeSegment.setup — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-019."
        )

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Label:
        """Segment one image using the model loaded in :meth:`setup`.

        Args:
            item: Input :class:`Image`.
            config: BlockConfig with cellpose params.
            state: The cellpose model returned by :meth:`setup` —
                must NOT be ``None`` here.

        Returns:
            A :class:`Label` whose ``raster`` slot holds the integer
            mask, with ``Label.Meta.n_objects`` populated.

        Raises:
            RuntimeError: If called with ``state=None`` (lifecycle bug).
        """
        raise NotImplementedError(
            "T-IMG-019 CellposeSegment.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-019."
        )

    def teardown(self, state: Any) -> None:
        """Release model state and free GPU memory when applicable (Q-IMG-2).

        ADR-027 D7: runs in a ``finally`` block even on error. The
        impl should call ``torch.cuda.empty_cache()`` when torch+CUDA
        are available, no-op otherwise.
        """
        raise NotImplementedError(
            "T-IMG-019 CellposeSegment.teardown — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-019."
        )
