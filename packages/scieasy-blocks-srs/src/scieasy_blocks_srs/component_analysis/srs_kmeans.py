"""SRSKMeansCluster — k-means clustering of pixel spectra → :class:`Label`.

Two outputs: a :class:`Label` raster and a centroid :class:`DataFrame`
indexed by ``cluster_id``. Overrides :meth:`run` directly.

Skeleton placeholder — T-SRS-010 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-010.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy_blocks_imaging.types import Label  # type: ignore[import-not-found]

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_srs.types import SRSImage

ALLOWED_INIT: tuple[str, ...] = ("k-means++", "random")


class SRSKMeansCluster(ProcessBlock):
    """K-means clustering of per-pixel spectra into a :class:`Label`."""

    name: ClassVar[str] = "SRS K-Means Cluster"
    description: ClassVar[str] = "K-means clustering of per-pixel spectra."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "component_analysis"
    algorithm: ClassVar[str] = "kmeans"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="labels",
            accepted_types=[Label],
            description="Label raster of cluster assignments (int32).",
        ),
        OutputPort(
            name="centroids",
            accepted_types=[DataFrame],
            description="Centroid DataFrame with `cluster_id` index.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "n_clusters": {"type": "integer", "default": 4, "minimum": 2},
            "init": {
                "type": "string",
                "enum": list(ALLOWED_INIT),
                "default": "k-means++",
            },
            "n_init": {"type": "integer", "default": 10, "minimum": 1},
        },
    }

    def run(
        self,
        inputs: dict[str, Any],
        config: BlockConfig,
    ) -> dict[str, Any]:
        """Reshape ``(n_pixels, n_w)``, fit KMeans, build Label + centroids.

        T-SRS-010 impl agent: ``sklearn.cluster.KMeans(n_clusters, init,
        n_init, random_state=42).fit_predict``, reshape labels to ``(y, x)``,
        cast to ``int32``, wrap in ``Label(raster=..., polygons=None)``,
        return centroid DataFrame with ``cluster_id`` index.
        """
        raise NotImplementedError(
            "T-SRS-010: SRSKMeansCluster.run — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-010."
        )


__all__ = ["ALLOWED_INIT", "SRSKMeansCluster"]
