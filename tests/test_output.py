from __future__ import annotations

from subprocess import TimeoutExpired
from unittest.mock import MagicMock, patch

import pytest

from chronoplay.output import (
    FFmpegOutput,
    OutputConfig,
    OutputConfigurationError,
    OutputError,
    OutputState,
)


def make_output(
    command: tuple[str, ...] = ("ffmpeg",),
) -> FFmpegOutput:
    """Create a test output."""
    return FFmpegOutput(OutputConfig(command=command))


def test_output_config_accepts_valid_command() -> None:
    """A valid command should create an output configuration."""
    config = OutputConfig(command=("ffmpeg", "-re"))

    assert config.command == ("ffmpeg", "-re")
    assert config.name == "ffmpeg"
    assert config.environment == {}
    assert config.working_directory is None


def test_output_config_accepts_environment() -> None:
    """Output configuration should preserve environment variables."""
    config = OutputConfig(
        command=("ffmpeg",),
        environment={"CHRONOPLAY_OUTPUT": "test"},
    )

    assert config.environment == {"CHRONOPLAY_OUTPUT": "test"}


def test_output_config_accepts_working_directory() -> None:
    """Output configuration should preserve its working directory."""
    config = OutputConfig(
        command=("ffmpeg",),
        working_directory="/media",
    )

    assert config.working_directory == "/media"


def test_output_config_rejects_empty_command() -> None:
    """An empty command should raise OutputConfigurationError."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output command cannot be empty",
    ):
        OutputConfig(command=())


def test_output_config_rejects_empty_command_part() -> None:
    """An empty command argument should raise OutputConfigurationError."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output command cannot be empty",
    ):
        OutputConfig(command=("ffmpeg", ""))


def test_output_config_rejects_empty_name() -> None:
    """An empty output name should raise OutputConfigurationError."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output name cannot be empty",
    ):
        OutputConfig(command=("ffmpeg",), name="")


def test_output_starts_stopped() -> None:
    """A new output should be stopped."""
    output = make_output()

    assert output.state is OutputState.STOPPED
    assert output.process is None
    assert output.last_error is None


def test_output_rejects_empty_media_path() -> None:
    """An empty media path should be rejected."""
    output = make_output()

    with pytest.raises(
        OutputConfigurationError,
        match="Media path cannot be empty",
    ):
        output.start("")


def test_output_rejects_whitespace_media_path() -> None:
    """A whitespace-only media path should be rejected."""
    output = make_output()

    with pytest.raises(
        OutputConfigurationError,
        match="Media path cannot be empty",
    ):
        output.start("   ")


@patch("chronoplay.output.Popen")
def test_output_start_sets_running_state(
    mock_popen: MagicMock,
) -> None:
    """Starting a valid output should set its state to running."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")

    assert output.state is OutputState.RUNNING
    assert output.process is process
    assert output.last_error is None


@patch("chronoplay.output.Popen")
def test_output_start_appends_media_path(
    mock_popen: MagicMock,
) -> None:
    """The media path should be appended to the configured command."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = make_output(("ffmpeg", "-re"))
    output.start("/media/program.mp4")

    command = mock_popen.call_args.args[0]

    assert command == [
        "ffmpeg",
        "-re",
        "/media/program.mp4",
    ]


@patch("chronoplay.output.Popen")
def test_output_start_merges_environment(
    mock_popen: MagicMock,
) -> None:
    """Configured environment variables should be passed to the process."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = FFmpegOutput(
        OutputConfig(
            command=("ffmpeg",),
            environment={"CHRONOPLAY_OUTPUT": "test"},
        )
    )

    output.start("/media/program.mp4")

    environment = mock_popen.call_args.kwargs["env"]

    assert environment is not None
    assert environment["CHRONOPLAY_OUTPUT"] == "test"


@patch("chronoplay.output.Popen")
def test_output_start_failure_sets_failed_state(
    mock_popen: MagicMock,
) -> None:
    """A process startup failure should set the failed state."""
    mock_popen.side_effect = OSError("ffmpeg unavailable")

    output = make_output()

    with pytest.raises(
        OutputError,
        match="Unable to start output backend",
    ):
        output.start("/media/program.mp4")

    assert output.state is OutputState.FAILED
    assert output.process is None
    assert output.last_error == "ffmpeg unavailable"


@patch("chronoplay.output.Popen")
def test_output_cannot_start_twice(
    mock_popen: MagicMock,
) -> None:
    """A running output cannot be started again."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")

    with pytest.raises(
        OutputError,
        match="already running",
    ):
        output.start("/media/second.mp4")

    assert mock_popen.call_count == 1


@patch("chronoplay.output.Popen")
def test_output_stop_terminates_process(
    mock_popen: MagicMock,
) -> None:
    """Stopping a running output should terminate its process."""
    process = MagicMock()
    process.poll.return_value = None
    process.returncode = 0
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")
    output.stop()

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)
    assert output.state is OutputState.STOPPED
    assert output.process is None


def test_output_stop_without_process_is_safe() -> None:
    """Stopping an inactive output should be safe."""
    output = make_output()

    output.stop()

    assert output.state is OutputState.STOPPED
    assert output.process is None


@patch("chronoplay.output.Popen")
def test_output_stop_kills_process_after_timeout(
    mock_popen: MagicMock,
) -> None:
    """An unresponsive process should be killed."""
    process = MagicMock()
    process.poll.return_value = None
    process.returncode = 0
    process.wait.side_effect = [
        TimeoutExpired("ffmpeg", 5),
        None,
    ]
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")
    output.stop()

    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert output.state is OutputState.STOPPED
    assert output.process is None


@patch("chronoplay.output.Popen")
def test_output_stop_records_process_failure(
    mock_popen: MagicMock,
) -> None:
    """A failed process should put the output into FAILED."""
    process = MagicMock()
    process.poll.return_value = 1
    process.returncode = 1
    process.stderr.read.return_value = "ffmpeg failed"
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")
    output.stop()

    assert output.state is OutputState.FAILED
    assert output.last_error == "ffmpeg failed"
    assert output.process is None


def test_output_health_is_false_when_stopped() -> None:
    """A stopped output should not be healthy."""
    output = make_output()

    assert output.health() is False


@patch("chronoplay.output.Popen")
def test_output_health_is_true_when_running(
    mock_popen: MagicMock,
) -> None:
    """A running process should report healthy."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")

    assert output.health() is True
    assert output.state is OutputState.RUNNING


@patch("chronoplay.output.Popen")
def test_output_health_detects_process_failure(
    mock_popen: MagicMock,
) -> None:
    """Health should detect when the process has exited."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = make_output()
    output.start("/media/program.mp4")

    process.poll.return_value = 1
    process.stderr.read.return_value = "unexpected termination"

    assert output.health() is False
    assert output.state is OutputState.FAILED
    assert output.last_error == "unexpected termination"
    assert output.process is None


def test_output_configuration_is_immutable() -> None:
    """OutputConfig should be immutable."""
    config = OutputConfig(command=("ffmpeg",))

    with pytest.raises(AttributeError):
        config.name = "changed"  # type: ignore[misc]
