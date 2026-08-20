import subprocess
import sys


def test_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "chronoplay", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout
