"""Subprocess entry point — invoked by spawn_block_process().

ADR-017: All block execution happens in isolated subprocesses. This module
is the entry point for those subprocesses.

Protocol:
    1. Receives serialized payload via stdin:
       - block_class: str (dotted module path + class name)
       - inputs_refs: dict[str, StorageReference serialization]
       - config: dict[str, Any]
    2. Reconstructs ViewProxy instances from StorageReferences.
    3. Imports block class, instantiates, calls block.run(inputs, config).
    4. Performs final force-write scan (_auto_flush) on all outputs.
    5. Returns output StorageReference pointers via stdout (JSON).
    6. On error: serializes traceback, returns error payload.
"""

from __future__ import annotations

from typing import Any


def main() -> None:
    """Subprocess entry point.

    TODO(ADR-017): Implement the subprocess worker protocol.

    Steps:
        1. Read JSON payload from stdin.
        2. Parse block_class path, inputs_refs, config.
        3. Import the block class via importlib.
        4. For each input ref, construct a ViewProxy from StorageReference.
        5. Instantiate block, call block.run(inputs, config).
        6. For each output DataObject:
           - If it has no StorageReference, call _auto_flush() to persist it
             (ADR-020-Add5: final force-write scan).
           - Collect output StorageReference pointers.
        7. Write JSON result to stdout: {"outputs": {port: ref_dict, ...}}.
        8. On exception: write {"error": traceback_str} to stdout.
    """
    raise NotImplementedError


def reconstruct_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct ViewProxy instances from serialized StorageReferences.

    TODO(ADR-017): For each input in payload["inputs_refs"]:
        - Deserialize StorageReference
        - Build TypeSignature from metadata
        - Create ViewProxy(storage_ref, dtype_info)
    """
    raise NotImplementedError


def serialise_outputs(outputs: dict[str, Any], output_dir: str) -> dict[str, Any]:
    """Serialize block outputs to StorageReference pointers.

    TODO(ADR-017, ADR-020-Add5): For each output DataObject:
        - If it has a StorageReference, use it directly.
        - Otherwise, call _auto_flush() to write to output_dir.
        - Return dict of port_name → serialized StorageReference.
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
