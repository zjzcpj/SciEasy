"""EnvironmentSnapshot — captures Python version, key packages, and full freeze."""

from __future__ import annotations

import contextlib
import platform as platform_mod
import sys
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version


@dataclass
class EnvironmentSnapshot:
    """Frozen snapshot of the execution environment at the time a block ran.

    Attributes:
        python_version: Python interpreter version string.
        platform: OS / platform identifier.
        key_packages: Mapping of package name to version for critical dependencies.
        full_freeze: Optional ``pip freeze`` output.
        conda_env: Optional conda environment export.
    """

    python_version: str
    platform: str
    key_packages: dict[str, str] = field(default_factory=dict)
    full_freeze: str | None = None
    conda_env: str | None = None

    @classmethod
    def capture(cls, key_dependencies: list[str] | None = None) -> EnvironmentSnapshot:
        """Capture the current runtime environment.

        Args:
            key_dependencies: Package names whose versions should be recorded
                in :attr:`key_packages`. Defaults to core SciEasy dependencies.
        """
        if key_dependencies is None:
            key_dependencies = ["scieasy", "numpy", "zarr", "pyarrow", "pydantic"]

        key_packages: dict[str, str] = {}
        for pkg in key_dependencies:
            with contextlib.suppress(PackageNotFoundError):
                key_packages[pkg] = version(pkg)

        return cls(
            python_version=sys.version,
            platform=platform_mod.platform(),
            key_packages=key_packages,
        )
