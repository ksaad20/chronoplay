from chronoplay.cli.commands import main


def test_cli_help(capsys):
    result = main(["--help"])

    assert result == 0

    captured = capsys.readouterr()
    assert "ChronoPlay" in captured.out
