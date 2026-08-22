from pathlib import Path

from chronoplay import __version__
from chronoplay.cli.commands import build_parser, main


def test_build_parser_has_expected_program_and_description():
    parser = build_parser()

    assert parser.prog == "chronoplay"
    assert "ChronoPlay" in parser.description


def test_parser_help(capsys):
    parser = build_parser()

    parser.print_help()

    captured = capsys.readouterr()

    assert "ChronoPlay" in captured.out
    assert "--version" in captured.out
    assert "--config" in captured.out
    assert "--schedule" in captured.out
    assert "--channel" in captured.out
    assert "--validate" in captured.out
    assert "--dry-run" in captured.out
    assert "demo" in captured.out


def test_version(capsys):
    parser = build_parser()

    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()

    assert f"ChronoPlay {__version__}" in captured.out


def test_config_argument():
    parser = build_parser()

    args = parser.parse_args(["--config", "config.yaml"])

    assert args.config == "config.yaml"


def test_schedule_argument():
    parser = build_parser()

    args = parser.parse_args(["--schedule", "schedule.yaml"])

    assert args.schedule == "schedule.yaml"


def test_channel_argument():
    parser = build_parser()

    args = parser.parse_args(["--channel", "main"])

    assert args.channel == "main"


def test_validate_flag():
    parser = build_parser()

    args = parser.parse_args(["--validate"])

    assert args.validate is True


def test_dry_run_flag():
    parser = build_parser()

    args = parser.parse_args(["--dry-run"])

    assert args.dry_run is True


def test_default_arguments():
    parser = build_parser()

    args = parser.parse_args([])

    assert args.config is None
    assert args.schedule is None
    assert args.channel is None
    assert args.validate is False
    assert args.dry_run is False
    assert args.command is None


def test_demo_parser():
    parser = build_parser()

    args = parser.parse_args(["demo", "program.mp4"])

    assert args.command == "demo"
    assert args.media_path == Path("program.mp4")
    assert callable(args.func)


def test_demo_parser_accepts_path_with_spaces():
    parser = build_parser()

    args = parser.parse_args(["demo", "my program.mp4"])

    assert args.command == "demo"
    assert args.media_path == Path("my program.mp4")


def test_main_without_arguments_returns_zero(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["chronoplay"],
    )

    assert main() == 0


def test_main_with_global_arguments_returns_zero(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "chronoplay",
            "--config",
            "config.yaml",
            "--schedule",
            "schedule.yaml",
            "--channel",
            "main",
            "--validate",
            "--dry-run",
        ],
    )

    assert main() == 0


def test_demo_command_calls_run_demo(monkeypatch, tmp_path):
    media_path = tmp_path / "program.mp4"
    calls = []

    def fake_run_demo(path):
        calls.append(path)

    monkeypatch.setattr(
        "chronoplay.cli.commands.run_demo",
        fake_run_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["chronoplay", "demo", str(media_path)],
    )

    assert main() == 0
    assert calls == [media_path]


def test_demo_command_uses_path_object(monkeypatch, tmp_path):
    media_path = tmp_path / "broadcast.mp4"
    received = []

    def fake_run_demo(path):
        received.append(path)

    monkeypatch.setattr(
        "chronoplay.cli.commands.run_demo",
        fake_run_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["chronoplay", "demo", str(media_path)],
    )

    main()

    assert len(received) == 1
    assert isinstance(received[0], Path)
    assert received[0] == media_path
