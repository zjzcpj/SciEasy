"""Tests for _native_dialog_windows: modern IFileOpenDialog COM folder picker."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.skipif(
    __import__("sys").platform != "win32",
    reason="Windows-only dialog",
)
class TestNativeDialogWindowsDirectory:
    """Verify that the directory branch uses the modern IFileOpenDialog COM dialog."""

    def test_directory_mode_uses_ifileopendialog(self) -> None:
        """The PowerShell script should compile a C# FolderPicker via Add-Type,
        NOT use the legacy FolderBrowserDialog."""
        from scieasy.api.routes.filesystem import _native_dialog_windows

        mock_result = MagicMock()
        mock_result.stdout = r"C:\Users\test\Documents"
        mock_result.returncode = 0

        with patch("scieasy.api.routes.filesystem.subprocess.run", return_value=mock_result) as mock_run:
            result = _native_dialog_windows("directory", None)

        mock_run.assert_called_once()
        ps_command = mock_run.call_args[0][0]
        ps_script = ps_command[-1]  # last arg is the -Command value

        # Must use IFileOpenDialog COM approach, not FolderBrowserDialog
        assert "FolderPicker" in ps_script
        assert "IFileDialog" in ps_script
        assert "Add-Type -TypeDefinition" in ps_script
        assert "FolderBrowserDialog" not in ps_script

        assert result == [r"C:\Users\test\Documents"]

    def test_directory_mode_cancel_returns_empty(self) -> None:
        """When the user cancels, the function should return an empty list."""
        from scieasy.api.routes.filesystem import _native_dialog_windows

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("scieasy.api.routes.filesystem.subprocess.run", return_value=mock_result):
            result = _native_dialog_windows("directory", None)

        assert result == []

    def test_file_mode_uses_openfiledialog(self) -> None:
        """The file branch should still use OpenFileDialog (not IFileOpenDialog)."""
        from scieasy.api.routes.filesystem import _native_dialog_windows

        mock_result = MagicMock()
        mock_result.stdout = r"C:\file1.txt|C:\file2.txt"
        mock_result.returncode = 0

        with patch("scieasy.api.routes.filesystem.subprocess.run", return_value=mock_result) as mock_run:
            result = _native_dialog_windows("file", None)

        ps_command = mock_run.call_args[0][0]
        ps_script = ps_command[-1]

        assert "OpenFileDialog" in ps_script
        assert "FolderPicker" not in ps_script
        assert result == [r"C:\file1.txt", r"C:\file2.txt"]
