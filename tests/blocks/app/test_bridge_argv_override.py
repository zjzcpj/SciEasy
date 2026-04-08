"""Test FileExchangeBridge.launch argv_override parameter (#420)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from scieasy.blocks.app.bridge import FileExchangeBridge


def test_launch_appends_exchange_dir_by_default(tmp_path: Path) -> None:
    """When argv_override is None, launch appends str(exchange_dir) to argv."""
    bridge = FileExchangeBridge()
    exchange = tmp_path / "exchange"
    exchange.mkdir()

    with patch("scieasy.blocks.app.bridge.subprocess.Popen") as mock_popen:
        mock_popen.return_value = mock_popen
        bridge.launch([sys.executable, "-c", "pass"], exchange)

    args_used = mock_popen.call_args[0][0]
    assert args_used[-1] == str(exchange)


def test_launch_uses_argv_override_when_provided(tmp_path: Path) -> None:
    """When argv_override is given, those args replace the default exchange_dir suffix."""
    bridge = FileExchangeBridge()
    exchange = tmp_path / "exchange"
    exchange.mkdir()
    override = ["/some/file.tif", "/other/file.tif"]

    with patch("scieasy.blocks.app.bridge.subprocess.Popen") as mock_popen:
        mock_popen.return_value = mock_popen
        bridge.launch([sys.executable, "-c", "pass"], exchange, argv_override=override)

    args_used = mock_popen.call_args[0][0]
    assert args_used[-2:] == override
    assert str(exchange) not in args_used
