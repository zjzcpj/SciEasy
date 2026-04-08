"""SRSVCA — Vertex Component Analysis endmember extraction.

Walks the data simplex (Nascimento & Bioucas-Dias 2005) to pick
``n_components`` endmember spectra. The module-level helper
:func:`_extract_endmembers` is the test seam reused by :class:`SRSUnmix`
when no reference DataFrame is supplied.

Skeleton placeholder — T-SRS-006 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-006.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_srs.types import SRSImage


def _extract_endmembers(
    item: SRSImage,
    n_components: int,
) -> tuple[np.ndarray, list[float]]:
    """Run VCA on ``item`` and return ``(endmembers, wavenumbers)``.

    Module-level helper so that :class:`SRSUnmix` can reuse it for the
    auto-VCA fallback (spec §8 Question 4). Output endmember matrix has
    shape ``(n_components, n_w)`` and lists the **original** full-dimension
    pixel spectra at the chosen indices. Wavenumbers come from
    ``item.meta.wavenumbers_cm1`` if set, else ``list(range(n_w))``.

    T-SRS-006 impl agent: PCA pre-reduce → VCA simplex walk
    (``random_state=42``) → return original-dim spectra at chosen indices.
    """
    raise NotImplementedError(
        "T-SRS-006: _extract_endmembers — impl pending (skeleton). "
        "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-006."
    )


class SRSVCA(ProcessBlock):
    """Endmember extraction via Vertex Component Analysis."""

    name: ClassVar[str] = "SRS VCA"
    description: ClassVar[str] = "Vertex Component Analysis endmember extraction."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "component_analysis"
    algorithm: ClassVar[str] = "vca"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="endmembers",
            accepted_types=[DataFrame],
            description="DataFrame with `endmember_id` index and wavenumber columns.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "n_components": {"type": "integer", "default": 4, "minimum": 2},
        },
    }

    def process_item(
        self,
        item: SRSImage,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        """Call :func:`_extract_endmembers` and wrap as a SciEasy DataFrame.

        T-SRS-006 impl agent: assemble a ``pandas.DataFrame`` with
        ``columns = wavenumbers``, ``index = pd.Index(range(n),
        name="endmember_id")``, then ``DataFrame.from_pandas(df)``.
        """
        raise NotImplementedError(
            "T-SRS-006: SRSVCA.process_item — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-006."
        )


__all__ = ["SRSVCA", "_extract_endmembers"]
