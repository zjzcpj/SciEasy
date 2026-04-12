# Publishing

This document covers how to package and distribute SciEasy blocks as
installable Python packages (Tier 2 distribution).

---

## Table of Contents

1. [Distribution Tiers](#distribution-tiers)
2. [Package Structure](#package-structure)
3. [pyproject.toml](#pyprojecttoml)
4. [Entry-Points](#entry-points)
5. [PackageInfo Declaration](#packageinfo-declaration)
6. [get_blocks() and get_types()](#get_blocks-and-get_types)
7. [Testing Before Release](#testing-before-release)
8. [Versioning](#versioning)
9. [Optional Dependencies](#optional-dependencies)

---

## Distribution Tiers

### Tier 1: Drop-in files

Place `.py` files in `~/.scieasy/blocks/` or a project's `blocks/`
directory. No packaging needed. Good for personal blocks or prototyping.

### Tier 2: Installable packages

Distribute via PyPI (or private index). Users install with
`pip install your-package`. Good for shared, versioned, tested blocks.

---

## Package Structure

Follow the standard `src/` layout:

```
my-blocks/
  pyproject.toml
  README.md
  src/
    my_blocks/
      __init__.py          # get_blocks(), get_types(), get_block_package()
      blocks/
        __init__.py
        my_process.py      # ProcessBlock subclass
        my_loader.py       # IOBlock subclass
      types/
        __init__.py
        my_types.py        # Custom Array/DataFrame subclasses
  tests/
    __init__.py
    conftest.py
    test_my_process.py
    test_my_loader.py
```

---

## pyproject.toml

Minimal example:

```toml
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "scieasy-blocks-mypackage"
version = "0.1.0"
description = "My custom blocks for SciEasy."
readme = "README.md"
authors = [
    {name = "Your Name"},
]
requires-python = ">=3.11"
dependencies = [
    "scieasy>=0.2.1",
    "numpy>=1.24",
]

[project.entry-points."scieasy.blocks"]
mypackage = "my_blocks:get_block_package"

[project.entry-points."scieasy.types"]
mypackage = "my_blocks:get_types"

[tool.hatch.build.targets.wheel]
packages = ["src/my_blocks"]
```

---

## Entry-Points

SciEasy discovers blocks and types via two entry-point groups:

### `scieasy.blocks`

The block registry scans this group at startup. Each entry-point must
point to a callable that returns either:

- `(PackageInfo, list[type[Block]])` -- recommended format.
- `list[type[Block]]` -- backward-compatible format.

```toml
[project.entry-points."scieasy.blocks"]
mypackage = "my_blocks:get_block_package"
```

### `scieasy.types`

The type registry scans this group at startup. Each entry-point must
point to a callable that returns `list[type]`:

```toml
[project.entry-points."scieasy.types"]
mypackage = "my_blocks:get_types"
```

---

## PackageInfo Declaration

`PackageInfo` is a frozen dataclass that describes your package to the
registry:

```python
from scieasy.blocks.base.package_info import PackageInfo

info = PackageInfo(
    name="scieasy-blocks-mypackage",
    description="My custom processing blocks.",
    author="Your Name",
    version="0.1.0",
)
```

Fields:

| Field | Required | Default |
|-------|----------|---------|
| `name` | Yes | -- |
| `description` | No | `""` |
| `author` | No | `""` |
| `version` | No | `"0.1.0"` |

---

## get_blocks() and get_types()

Your package's `__init__.py` should export three callables:

```python
"""My blocks package."""

from __future__ import annotations

from scieasy.blocks.base.package_info import PackageInfo
from my_blocks.blocks.my_process import MyProcessBlock
from my_blocks.blocks.my_loader import MyLoader
from my_blocks.types.my_types import MyImage

__version__ = "0.1.0"

_TYPES: tuple[type, ...] = (MyImage,)
_BLOCKS: tuple[type, ...] = (MyProcessBlock, MyLoader)


def get_package_info() -> PackageInfo:
    return PackageInfo(
        name="scieasy-blocks-mypackage",
        description="My custom blocks.",
        author="Your Name",
        version=__version__,
    )


def get_types() -> list[type]:
    """Return exported type classes for the scieasy.types entry-point."""
    return list(_TYPES)


def get_blocks() -> list[type]:
    """Return exported block classes."""
    return list(_BLOCKS)


def get_block_package() -> tuple[PackageInfo, list[type]]:
    """Return package metadata and blocks for scieasy.blocks entry-point."""
    return get_package_info(), get_blocks()
```

---

## Testing Before Release

Run the full validation before publishing:

```python
from scieasy.testing import BlockTestHarness
from scieasy.blocks.base.block import Block

def test_entry_point_validates():
    from my_blocks import get_block_package
    harness = BlockTestHarness(Block)
    result = get_block_package()
    errors = harness.validate_entry_point_callable(result)
    assert not errors, "\n".join(errors)

def test_all_blocks_contract():
    from my_blocks import get_blocks
    for block_cls in get_blocks():
        harness = BlockTestHarness(block_cls)
        errors = harness.validate_block()
        assert not errors, f"{block_cls.__name__}: {errors}"

def test_types_registered():
    from my_blocks import get_types
    types = get_types()
    assert len(types) > 0
    for t in types:
        assert isinstance(t, type)
```

---

## Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes to block contract (port names, types,
  config schema changes that break existing workflows).
- **MINOR**: New blocks, new optional config fields, new types.
- **PATCH**: Bug fixes, documentation, internal improvements.

---

## Optional Dependencies

For blocks with heavy dependencies (e.g., ML frameworks), use optional
dependency groups:

```toml
[project.optional-dependencies]
gpu = [
    "torch>=2.0",
    "cellpose>=3.0",
]
```

In your block, import lazily and raise a clear error:

```python
def setup(self, config):
    try:
        from cellpose import models
    except ImportError as exc:
        raise ImportError(
            "This block requires the [gpu] extra: "
            "pip install scieasy-blocks-mypackage[gpu]"
        ) from exc
    return models.Cellpose(model_type=config.get("model"))
```

Use `key_dependencies` to display requirements in the UI:

```python
key_dependencies: ClassVar[list[str]] = ["cellpose>=3.0", "torch>=2.0"]
```
