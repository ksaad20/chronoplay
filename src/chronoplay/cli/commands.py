from __future__ import annotations

import argparse
import runpy
from pathlib import Path
from unittest.mock import patch

from chronoplay import __version__
from chronoplay.demo import run_demo


def test_commands_main_execution():
    """Test executing chronoplay.cli.commands directly."""
    with patch("chronoplay.cli.commands.main", return_value=0) as mock_main:
        runpy.run_module("chronoplay.cli.commands", run_name="__main__")
        mock_main.assert_called_once()

def _run_demo(media_path: Path) -> None:
    """Run the ChronoPlay demonstration."""
    run_demo(media_path)


def build_parser() -> argparse.ArgumentParser:
    """Build the ChronoPlay command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="chronoplay",
        description=(
            "ChronoPlay: cross-platform, time-synchronized, "
            "broadcast playout and scheduling system."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"ChronoPlay {__version__}",
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to the ChronoPlay configuration file.",
    )

    parser.add_argument(
        "--schedule",
        metavar="PATH",
        help="Path to the YAML broadcast schedule.",
    )

    parser.add_argument(
        "--channel",
        metavar="ID",
        help="Channel identifier to operate on.",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and schedule without starting playout.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the resolved schedule without executing playout.",
    )

    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser(
        "demo",
        help="Run a ChronoPlay demonstration.",
        description="Run a ChronoPlay demonstration using a media file.",
    )
    demo_parser.add_argument(
        "media_path",
        type=Path,
        help="Path to the media file used for the demonstration.",
    )
    demo_parser.set_defaults(func=_run_demo)

    return parser


def main() -> int:
    """Run the ChronoPlay command-line interface."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "demo":
        args.func(args.media_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
