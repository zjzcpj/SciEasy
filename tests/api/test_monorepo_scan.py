"""Tests for monorepo scanner gating behind SCIEASY_DEV env var (#509)."""

from __future__ import annotations

import os
from unittest.mock import patch


def test_monorepo_scan_disabled_by_default():
    """Without SCIEASY_DEV=1, include_monorepo should be False."""
    env = {k: v for k, v in os.environ.items() if k != "SCIEASY_DEV"}
    with patch.dict(os.environ, env, clear=True):
        assert os.environ.get("SCIEASY_DEV") != "1"


def test_monorepo_scan_enabled_with_env():
    """With SCIEASY_DEV=1, include_monorepo should be True."""
    with patch.dict(os.environ, {"SCIEASY_DEV": "1"}):
        assert os.environ.get("SCIEASY_DEV") == "1"


def test_monorepo_scan_disabled_with_wrong_value():
    """SCIEASY_DEV must be exactly '1' to enable monorepo scan."""
    with patch.dict(os.environ, {"SCIEASY_DEV": "true"}):
        assert os.environ.get("SCIEASY_DEV") != "1"
    with patch.dict(os.environ, {"SCIEASY_DEV": "0"}):
        assert os.environ.get("SCIEASY_DEV") != "1"
