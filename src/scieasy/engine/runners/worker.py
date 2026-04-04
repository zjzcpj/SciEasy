"""Subprocess entry point — invoked by spawn_block_process().

ADR-017: All block execution happens in isolated subprocesses. This module
is the entry point for those subprocesses.

Protocol:
    1. Receives serialized payload via stdin:
       - block_class: str (dotted module path + class name)
       - inputs: dict[str, Any] (input references)
       - config: dict[str, Any]
       - output_dir: str (optional, for persisting outputs)
    2. Reconstructs inputs from payload.
    3. Imports block class, instantiates, calls block.run(inputs, config).
    4. Serializes outputs and writes JSON result to stdout.
    5. On error: serializes traceback, returns error payload, exits with code 1.
"""

from __future__ import annotations

import importlib
import json
import sys
import traceback
from typing import Any


def reconstruct_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct inputs from serialized payload.

    TODO(ADR-017): Full ViewProxy reconstruction from StorageReference
    pointers will be implemented in a future phase. For now, inputs
    are passed through as-is from the payload.
    """
    return dict(payload.get("inputs", {}))


def serialise_outputs(outputs: dict[str, Any], output_dir: str) -> dict[str, Any]:
    """Serialize block outputs to JSON-compatible format.

    TODO(ADR-017, ADR-020-Add5): Full output serialization with
    StorageReference persistence and _auto_flush will be implemented
    in a future phase. For now, outputs with storage_ref are serialized
    to their reference dicts, and other values are stringified.

    Parameters
    ----------
    outputs:
        Mapping of port names to output data objects.
    output_dir:
        Directory for writing output artifacts (unused in basic mode).
    """
    result: dict[str, Any] = {}
    for key, value in outputs.items():
        if hasattr(value, "storage_ref") and value.storage_ref is not None:
            ref = value.storage_ref
            result[key] = {
                "backend": ref.backend,
                "path": ref.path,
                "format": ref.format,
            }
        else:
            result[key] = str(value)
    return result


def main() -> None:
    """Subprocess entry point.

    Steps:
        1. Read JSON payload from stdin.
        2. Parse block_class path, inputs, config.
        3. Import the block class via importlib.
        4. Reconstruct inputs from payload.
        5. Instantiate block, call block.run(inputs, config).
        6. Serialize outputs and write JSON to stdout.
        7. On exception: write {"error": traceback_str} to stdout, exit 1.
    """
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)

        block_class_path: str = payload["block_class"]
        config: dict[str, Any] = payload.get("config", {})
        output_dir: str = payload.get("output_dir", "")

        # Import block class
        module_path, class_name = block_class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        block_cls = getattr(module, class_name)

        # Reconstruct inputs
        inputs = reconstruct_inputs(payload)

        # Instantiate block
        block = block_cls()

        # Build config object
        from scieasy.blocks.base.config import BlockConfig

        block_config = BlockConfig(**config)

        # Execute
        outputs = block.run(inputs, block_config)

        # Serialize outputs
        result = serialise_outputs(outputs, output_dir) if isinstance(outputs, dict) else {"_result": str(outputs)}

        print(json.dumps({"outputs": result}))
    except Exception:
        print(json.dumps({"error": traceback.format_exc()}))
        sys.exit(1)


if __name__ == "__main__":
    main()
