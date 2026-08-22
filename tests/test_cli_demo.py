from __future__ import annotations

from unittest.mock import patch

from chronoplay.cli.commands import build_parser


def test_cli_parser_accepts_demo_command() -> None:
    """The CLI parser should accept the demo command."""
    parser = build_parser()

    with patch("chronoplay.cli.commands.run_demo") as mock_run_demo:
        args = parser.parse_args(["demo"])

        assert args.command == "demo"

        args.func()

        mock_run_demo.assert_called_once()


def test_cli_parser_accepts_demo_media_path() -> None:
    """The demo command should accept a media path."""
    parser = build_parser()

    args = parser.parse_args(["demo", "sample.mp4"])

    assert args.command == "demo"
    assert args.media_path == "sample.mp4"


def test_cli_parser_has_help_for_demo_command() -> None:
    """The demo command should expose help text."""
    parser = build_parser()

    with patch.object(parser, "print_help") as mock_print_help:
        args = parser.parse_args(["demo", "--help"])

        assert args is not None
        mock_print_help.assert_not_called()
