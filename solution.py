# src/scieasy/blocks/app/app_block.py

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

from scieasy.blocks.app.bridge import FileExchangeBridge
from scieasy.core import get_project_root  # Utility that returns the project workspace path


class AppBlock:
    """
    Represents a block that runs an external application and exchanges data via a
    dedicated file-based exchange directory kept in the project workspace rather than the
    system temporary folder.
    """

    def __init__(self, block_id: str, block_config: Dict[str, Any]):
        """
        Parameters
        ----------
        block_id : str
            Unique identifier for the block instance.
        block_config : dict
            Block-level configuration that may contain various runtime settings.
        """
        self.block_id = block_id
        self.block_config = block_config
        self.exchange_dir: Path | None = None

    def run(self) -> None:
        """
        Executes the external application. Creates a dedicated exchange directory
        under the project's data/exchange folder, writes input artifacts, launches
        the application and monitors for output artifacts.
        """
        # --------------------------------------------------------------------
        # 1. Create a persistent exchange directory in the project workspace
        # --------------------------------------------------------------------
        project_root = Path(get_project_root())
        exchange_base = project_root / "data" / "exchange" / f"{self.block_id}"
        exchange_base.mkdir(parents=True, exist_ok=True)

        # Subdirectories for input and output files
        inputs_dir = exchange_base / "inputs"
        outputs_dir = exchange_base / "outputs"
        inputs_dir.mkdir(exist_ok=True)
        outputs_dir.mkdir(exist_ok=True)

        self.exchange_dir = exchange_base

        # --------------------------------------------------------------------
        # 2. Serialize input data (manifest.json) that will be read by the external app
        # --------------------------------------------------------------------
        manifest_path = inputs_dir / "manifest.json"
        with manifest_path.open("w") as fp:
            json.dump(self.block_config, fp, indent=2)

        # --------------------------------------------------------------------
        # 3. Invoke the bridge logic to launch the external program
        # --------------------------------------------------------------------
        bridge = FileExchangeBridge(
            app_id=self.block_id,
            inputs_dir=inputs_dir.as_posix(),
            outputs_dir=outputs_dir.as_posix(),
            timeout=self.block_config.get("timeout", 3600),
        )
        bridge.prepare()
        bridge.run()

        # --------------------------------------------------------------------
        # 4. Cleanup: propagate outputs to the workspace and optionally delete exchange dir
        # --------------------------------------------------------------------
        # Copy outputs to desired location inside the project if needed
        # (implementation omitted – application-specific logic)

        # Optionally remove the exchange directory after completion
        # (Comment out if persistence across checkpoints is required)
        # shutil.rmtree(exchange_base)

    # ------------------------------------------------------------------------
    # Existing helper methods can remain unchanged
    # ------------------------------------------------------------------------