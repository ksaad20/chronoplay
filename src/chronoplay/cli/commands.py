from __future__ import annotations

import argparse

def build_parser() -> argparse.ArgumentParser:
    """Build the ChronoPlay command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="chronoplay",
        description="ChronoPlay broadcast playout and scheduling system.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="ChronoPlay 0.1.0",
    )

    return parser


def main() -> None:
    """Run the ChronoPlay command-line interface."""
    parser = build_parser()
    parser.parse_args()


if __name__ == "__main__":
    main()
