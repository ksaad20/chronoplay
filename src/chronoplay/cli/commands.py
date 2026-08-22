from __future__ import annotations

import argparse

from chronoplay import __version__
from chronoplay.demo import run_demo


def build_parser() -> argparse.ArgumentParser:
    """Build the ChronoPlay command-line parser."""
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
        version="chronoplay 0.0.1",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to the ChronoPlay configuration file.",
    )
    parser.add_argument(
        "--schedule",
        type=Path,
        help="Path to the schedule file.",
    )
    parser.add_argument(
        "--channel",
        help="Channel identifier.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the supplied configuration or schedule.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without starting playout.",
    )

    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser(
        "demo",
        help="Run a demonstration playout.",
        description="Run a ChronoPlay demonstration using a media file.",
    )
    demo_parser.add_argument(
        "media_path",
        type=Path,
        help="Path to the media file used for the demonstration.",
    )
    demo_parser.set_defaults(func=_run_demo)

    return parser


def _run_demo(args: argparse.Namespace) -> None:
    """Run the ChronoPlay demonstration command."""
    run_demo(args.media_path)


def main() -> None:
    """Run the ChronoPlay command-line interface."""
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

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
