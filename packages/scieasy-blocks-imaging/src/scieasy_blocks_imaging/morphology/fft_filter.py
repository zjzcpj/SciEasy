"""FFTFilter — frequency-domain low/high/band-pass (T-IMG-016).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-016.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class FFTFilter(ProcessBlock):
    """Frequency-domain filtering with circular masks."""

    type_name: ClassVar[str] = "imaging.fft_filter"
    name: ClassVar[str] = "FFT Filter"
    description: ClassVar[str] = "FFT lowpass / highpass / bandpass filter."
    category: ClassVar[str] = "morphology"
    algorithm: ClassVar[str] = "fft_filter"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["lowpass", "highpass", "bandpass"],
                "default": "lowpass",
            },
            "cutoff_low": {"type": "number", "default": 0.1},
            "cutoff_high": {"type": "number", "default": 0.5},
        },
        "required": ["type"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-016 FFTFilter.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-016."
        )
