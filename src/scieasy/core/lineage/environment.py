"""EnvironmentSnapshot — captures Python version, key packages, and full freeze."""

from __future__ import annotations

from dataclasses import dataclass, field


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
                in :attr:`key_packages`.
        """
        raise NotImplementedError
