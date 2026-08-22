import runpy
import sys
from unittest.mock import patch

def test_module_entry_point() -> None:
    # Simulates: python -m chronoplay --help
    with patch.object(sys, "argv", ["chronoplay", "--help"]):
        try:
            runpy.run_module("chronoplay.__main__", run_name="__main__")
        except SystemExit as exc:
            # --help flags naturally call sys.exit(0)
            assert exc.code == 0
