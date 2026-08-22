import runpy
import subprocess
import sys
from unittest.mock import patch


def test_main_module_execution():
    """Test executing chronoplay.__main__ directly."""
    with patch("chronoplay.cli.commands.main") as mock_main:
        runpy.run_module("chronoplay.__main__", run_name="__main__")
        mock_main.assert_called_once()

def test_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "chronoplay", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout
