"""SRSImage(Image) with required_axes={'y','x','lambda'} and the SRS-specific Meta Pydantic model (wavenumbers, laser_power, integration_time, digitizer_*, pump/stokes wavelength)."""


class SRSImage:
    """Placeholder for T-SRS-001 — SRSImage(Image) type class."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "T-SRS-001: SRSImage type is a Phase 11 placeholder; see "
            "docs/specs/phase11-srs-block-spec.md §9 T-SRS-001."
        )
