"""SRSPCA — Principal Component Analysis along the spectral axis.

Two outputs: per-PC ``Collection[Image]`` score maps + ``DataFrame`` of
loadings indexed by ``pc_id``. Overrides :meth:`run` directly.

Skeleton placeholder — T-SRS-008 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-008.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_srs.types import SRSImage


class SRSPCA(ProcessBlock):
    """PCA on per-pixel spectra of an :class:`SRSImage`."""

    name: ClassVar[str] = "SRS PCA"
    description: ClassVar[str] = "Principal Component Analysis on per-pixel spectra."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "component_analysis"
    algorithm: ClassVar[str] = "pca"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="pc_maps",
            accepted_types=[Collection],
            description="Collection[Image] of per-PC 2D score maps.",
        ),
        OutputPort(
            name="loadings",
            accepted_types=[DataFrame],
            description="Loadings DataFrame with `pc_id` index and wavenumber columns.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "n_components": {"type": "integer", "default": 5, "minimum": 1},
            "scale": {"type": "boolean", "default": True},
        },
    }

    def run(
        self,
        inputs: dict[str, Any],
        config: BlockConfig,
    ) -> dict[str, Any]:
        """Reshape, optionally scale, fit PCA, emit score maps + loadings.

        T-SRS-008 impl agent: validate ``n_components <= n_wavenumbers``,
        ``StandardScaler`` if ``scale``, ``PCA(n_components,
        random_state=42).fit_transform``, emit one 2D :class:`Image` per
        component, build loadings ``DataFrame`` with ``pc_id`` index.
        """
        raise NotImplementedError(
            "T-SRS-008: SRSPCA.run — impl pending (skeleton). See docs/specs/phase11-srs-block-spec.md §9 T-SRS-008."
        )


__all__ = ["SRSPCA"]
