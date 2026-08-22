"""Command-line interface for ChronoPlay."""

from __future__ import annotations

import argparse

from chronoplay import __version__
from chronoplay.demo import run_demo


def _run_demo(args: argparse.Namespace) -> None:
    """Run the ChronoPlay demonstration command."""
    run_demo(args.media_path)

def build_parser() -> argparse.ArgumentParser:
    """Build the ChronoPlay command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="chronoplay",
        description=(
            "ChronoPlay: cross-platform, time-synchronized, broadcast playout and scheduling system."
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

    return parser


def main() -> int:
    """Run the ChronoPlay command-line interface."""
    parser = build_parser()
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
