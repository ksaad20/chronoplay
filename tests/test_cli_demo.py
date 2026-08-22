from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from chronoplay.cli.commands import build_parser


def test_cli_parser_accepts_demo_command() -> None:
    """The CLI parser should accept the demo command."""
    parser = build_parser()

    args = parser.parse_args(["demo", "sample.mp4"])

    assert args.command == "demo"
    assert args.media_path == Path("sample.mp4")


def test_cli_demo_dispatches_to_run_demo() -> None:
    """The demo command should dispatch to run_demo."""
    parser = build_parser()

    with patch("chronoplay.cli.commands.run_demo") as mock_run_demo:
        args = parser.parse_args(["demo", "sample.mp4"])

        args.func(args.media_path)

        mock_run_demo.assert_called_once_with(Path("sample.mp4"))


def test_cli_demo_requires_media_path() -> None:
    """The demo command should require a media path."""
    parser = build_parser()

    with patch("argparse.ArgumentParser.error") as mock_error:
        parser.parse_args(["demo"])

        mock_error.assert_called_once()
