"""EnvironmentSnapshot — captures Python version, key packages, and full freeze."""

from __future__ import annotations

import contextlib
import platform as platform_mod
import sys
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict for subprocess transport."""
        return {
            "python_version": self.python_version,
            "platform": self.platform,
            "key_packages": dict(self.key_packages),
            "full_freeze": self.full_freeze,
            "conda_env": self.conda_env,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentSnapshot:
        """Reconstruct from a dict produced by :meth:`to_dict`."""
        return cls(
            python_version=data["python_version"],
            platform=data["platform"],
            key_packages=data.get("key_packages", {}),
            full_freeze=data.get("full_freeze"),
            conda_env=data.get("conda_env"),
        )
