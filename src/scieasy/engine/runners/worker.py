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

    ADR-017: Converts StorageReference dicts back into ViewProxy instances
    so block.run() receives lazy-loading accessors, not raw dicts.
    Scalar values and other non-reference inputs pass through as-is.
    """
    from scieasy.core.proxy import ViewProxy
    from scieasy.core.storage.ref import StorageReference
    from scieasy.core.types.base import TypeSignature

    raw_inputs = payload.get("inputs", {})
    result: dict[str, Any] = {}

    for key, value in raw_inputs.items():
        if isinstance(value, dict) and "backend" in value and "path" in value:
            # This is a serialized StorageReference — reconstruct ViewProxy.
            ref = StorageReference(
                backend=value["backend"],
                path=value["path"],
                format=value.get("format"),
                metadata=value.get("metadata"),
            )
            type_chain = value.get("metadata", {}).get("type_chain", ["DataObject"])
            sig = TypeSignature(type_chain=type_chain)
            result[key] = ViewProxy(storage_ref=ref, dtype_info=sig)
        else:
            # Scalar or other value — pass through.
            result[key] = value

    return result


def serialise_outputs(outputs: dict[str, Any], output_dir: str) -> dict[str, Any]:
    """Serialize block outputs to JSON-compatible format.

    ADR-017: Converts output DataObjects into StorageReference dicts.
    ADR-020-Add5: Auto-flushes in-memory DataObjects that lack a
    StorageReference, writing them to output_dir before serialization.

    Parameters
    ----------
    outputs:
        Mapping of port names to output data objects.
    output_dir:
        Directory for writing output artifacts when auto-flushing.
    """
    from scieasy.blocks.base.block import Block
    from scieasy.core.types.base import DataObject
    from scieasy.core.types.collection import Collection

    result: dict[str, Any] = {}
    for key, value in outputs.items():
        # Handle Collection: serialize each item's reference.
        if isinstance(value, Collection):
            item_refs = []
            for item in value:
                item = Block._auto_flush(item)
                if hasattr(item, "storage_ref") and item.storage_ref is not None:
                    ref = item.storage_ref
                    item_meta = {**(ref.metadata or {})}
                    if hasattr(item, "dtype_info"):
                        item_meta["type_chain"] = item.dtype_info.type_chain
                    item_refs.append(
                        {
                            "backend": ref.backend,
                            "path": ref.path,
                            "format": ref.format,
                            "metadata": item_meta,
                        }
                    )
                else:
                    item_refs.append({"_value": str(item)})
            result[key] = {
                "_collection": True,
                "items": item_refs,
                "item_type": value.item_type.__name__,
            }
            continue

        # Auto-flush in-memory DataObjects.
        if isinstance(value, DataObject):
            value = Block._auto_flush(value)

        # Serialize StorageReference-backed objects.
        if hasattr(value, "storage_ref") and value.storage_ref is not None:
            ref = value.storage_ref
            obj_meta = {**(ref.metadata or {})}
            if hasattr(value, "dtype_info"):
                obj_meta["type_chain"] = value.dtype_info.type_chain
            result[key] = {
                "backend": ref.backend,
                "path": ref.path,
                "format": ref.format,
                "metadata": obj_meta,
            }
        elif isinstance(value, (str, int, float, bool, type(None), list, dict)):
            result[key] = value
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

        # Capture environment inside subprocess for accurate lineage (issue #54).
        from scieasy.core.lineage.environment import EnvironmentSnapshot

        env_snapshot = EnvironmentSnapshot.capture()

        # Serialize outputs
        result = serialise_outputs(outputs, output_dir) if isinstance(outputs, dict) else {"_result": str(outputs)}

        print(json.dumps({"outputs": result, "environment": env_snapshot.to_dict()}))
    except Exception:
        print(json.dumps({"error": traceback.format_exc()}))
        sys.exit(1)


if __name__ == "__main__":
    main()
