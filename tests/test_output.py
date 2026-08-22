from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chronoplay.output import (
    FFmpegOutput,
    MediaOutput,
    OutputConfig,
    OutputConfigurationError,
    OutputError,
    OutputState,
)


def make_config(
    *,
    command: tuple[str, ...] = ("ffmpeg",),
    name: str = "test-output",
    environment: dict[str, str] | None = None,
    working_directory: str | None = None,
) -> OutputConfig:
    """Create a valid output configuration for testing."""
    return OutputConfig(
        command=command,
        name=name,
        environment=environment or {},
        working_directory=working_directory,
    )


def test_output_config_accepts_valid_command() -> None:
    """A valid command should create an OutputConfig."""
    config = make_config(command=("ffmpeg", "-version"))

    assert config.command == ("ffmpeg", "-version")
    assert config.name == "test-output"


def test_output_config_defaults_environment() -> None:
    """The default environment should be empty."""
    config = make_config()

    assert config.environment == {}


def test_output_config_accepts_environment() -> None:
    """Configured environment variables should be preserved."""
    config = make_config(
        environment={"CHRONOPLAY_OUTPUT": "test"},
    )

    assert config.environment == {"CHRONOPLAY_OUTPUT": "test"}


def test_output_config_accepts_working_directory(
    tmp_path: Path,
) -> None:
    """A working directory should be preserved."""
    config = make_config(
        working_directory=str(tmp_path),
    )

    assert config.working_directory == str(tmp_path)


def test_output_config_rejects_empty_command() -> None:
    """An empty command should be rejected."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output command cannot be empty",
    ):
        OutputConfig(command=())


def test_output_config_rejects_command_with_empty_argument() -> None:
    """A command containing an empty argument should be rejected."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output command cannot be empty",
    ):
        OutputConfig(command=("ffmpeg", ""))


def test_output_config_rejects_whitespace_command_argument() -> None:
    """A command containing whitespace-only arguments should be rejected."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output command cannot be empty",
    ):
        OutputConfig(command=("ffmpeg", "   "))


def test_output_config_rejects_empty_name() -> None:
    """An empty output name should be rejected."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output name cannot be empty",
    ):
        OutputConfig(command=("ffmpeg",), name="")


def test_output_config_rejects_whitespace_name() -> None:
    """A whitespace-only output name should be rejected."""
    with pytest.raises(
        OutputConfigurationError,
        match="Output name cannot be empty",
    ):
        OutputConfig(command=("ffmpeg",), name="   ")


def test_new_output_starts_stopped() -> None:
    """A new FFmpeg output should start in the stopped state."""
    output = FFmpegOutput(make_config())

    assert output.state is OutputState.STOPPED
    assert output.process is None
    assert output.last_error is None


def test_output_implements_media_output_protocol() -> None:
    """FFmpegOutput should satisfy the MediaOutput protocol."""
    output = FFmpegOutput(make_config())

    assert isinstance(output, MediaOutput)


def test_start_rejects_empty_media_path() -> None:
    """An empty media path should be rejected."""
    output = FFmpegOutput(make_config())

    with pytest.raises(
        OutputConfigurationError,
        match="Media path cannot be empty",
    ):
        output.start("")


def test_start_rejects_whitespace_media_path() -> None:
    """A whitespace-only media path should be rejected."""
    output = FFmpegOutput(make_config())

    with pytest.raises(
        OutputConfigurationError,
        match="Media path cannot be empty",
    ):
        output.start("   ")


@patch("chronoplay.output.Popen")
def test_start_launches_ffmpeg_process(
    mock_popen: MagicMock,
) -> None:
    """Starting output should launch FFmpeg with the media path."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = FFmpegOutput(
        make_config(command=("ffmpeg", "-re")),
    )

    output.start("/media/program.mp4")

    mock_popen.assert_called_once_with(
        ["ffmpeg", "-re", "/media/program.mp4"],
        cwd=None,
        env=None,
        stdout=-3,
        stderr=-1,
        text=True,
    )
    assert output.state is OutputState.RUNNING
    assert output.process is process
    assert output.last_error is None


@patch("chronoplay.output.Popen")
def test_start_passes_working_directory(
    mock_popen: MagicMock,
    tmp_path: Path,
) -> None:
    """The configured working directory should be passed to FFmpeg."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = FFmpegOutput(
        make_config(
            working_directory=str(tmp_path),
        ),
    )

    output.start("/media/program.mp4")

    assert mock_popen.call_args.kwargs["cwd"] == str(tmp_path)


@patch("chronoplay.output.Popen")
def test_start_merges_environment(
    mock_popen: MagicMock,
) -> None:
    """Configured environment variables should be merged with os.environ."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = FFmpegOutput(
        make_config(
            environment={"CHRONOPLAY_OUTPUT": "test"},
        ),
    )

    output.start("/media/program.mp4")

    environment = mock_popen.call_args.kwargs["env"]

    assert environment is not None
    assert environment["CHRONOPLAY_OUTPUT"] == "test"


@patch("chronoplay.output.Popen")
def test_start_sets_failed_state_when_process_cannot_start(
    mock_popen: MagicMock,
) -> None:
    """A process startup failure should put the output into FAILED."""
    mock_popen.side_effect = OSError("ffmpeg not found")

    output = FFmpegOutput(make_config())

    with pytest.raises(
        OutputError,
        match="Unable to start output backend",
    ):
        output.start("/media/program.mp4")

    assert output.state is OutputState.FAILED
    assert output.process is None
    assert output.last_error == "ffmpeg not found"


@patch("chronoplay.output.Popen")
def test_start_clears_previous_error(
    mock_popen: MagicMock,
) -> None:
    """A successful start should clear a previous backend error."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.side_effect = [
        OSError("first failure"),
        process,
    ]

    output = FFmpegOutput(make_config())

    with pytest.raises(OutputError):
        output.start("/media/program.mp4")

    assert output.state is OutputState.FAILED

    output.start("/media/program.mp4")

    assert output.state is OutputState.RUNNING
    assert output.last_error is None


@patch("chronoplay.output.Popen")
def test_start_rejects_already_running_output(
    mock_popen: MagicMock,
) -> None:
    """Starting an already-running output should raise OutputError."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = FFmpegOutput(make_config())

    output.start("/media/program.mp4")

    with pytest.raises(
        OutputError,
        match="already running",
    ):
        output.start("/media/second.mp4")

    assert mock_popen.call_count == 1


@patch("chronoplay.output.Popen")
def test_stop_terminates_running_process(
    mock_popen: MagicMock,
) -> None:
    """Stopping a running output should terminate its process."""
    process = MagicMock()
    process.poll.return_value = None
    process.returncode = 0
    mock_popen.return_value = process

    output = FFmpegOutput(make_config())
    output.start("/media/program.mp4")
    output.stop()

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)

    assert output.state is OutputState.STOPPED
    assert output.process is None


@patch("chronoplay.output.Popen")
def test_stop_is_safe_when_not_running(
    mock_popen: MagicMock,
) -> None:
    """Stopping an inactive output should be safe."""
    output = FFmpegOutput(make_config())

    output.stop()

    mock_popen.assert_not_called()
    assert output.state is OutputState.STOPPED
    assert output.process is None


@patch("chronoplay.output.Popen")
def test_stop_force_kills_unresponsive_process(
    mock_popen: MagicMock,
) -> None:
    """An unresponsive process should be killed after termination times out."""
    process = MagicMock()
    process.poll.return_value = None
    process.returncode = 0
    process.wait.side_effect = [
        __import__("subprocess").TimeoutExpired(
            cmd="ffmpeg",
            timeout=5,
        ),
        None,
    ]
    mock_popen.return_value = process

    output = FFmpegOutput(make_config())
    output.start("/media/program.mp4")
    output.stop()

    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    assert output.state is OutputState.STOPPED
    assert output.process is None


@patch("chronoplay.output.Popen")
def test_stop_failed_process_sets_failed_state(
    mock_popen: MagicMock,
) -> None:
    """A non-zero process exit should put the output into FAILED."""
    process = MagicMock()
    process.poll.return_value = 1
    process.returncode = 1
    process.stderr = MagicMock()
    process.stderr.read.return_value = "encoder failure"
    mock_popen.return_value = process

    output = FFmpegOutput(make_config())
    output.start("/media/program.mp4")
    output.stop()

    assert output.state is OutputState.FAILED
    assert output.last_error == "encoder failure"
    assert output.process is None


@patch("chronoplay.output.Popen")
def test_health_returns_true_for_running_process(
    mock_popen: MagicMock,
) -> None:
    """A live process should report healthy."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    output = FFmpegOutput(make_config())
    output.start("/media/program.mp4")

    assert output.health() is True
    assert output.state is OutputState.RUNNING
    assert output.process is process


def test_health_returns_false_when_stopped() -> None:
    """A stopped output should report unhealthy."""
    output = FFmpegOutput(make_config())

    assert output.health() is False
    assert output.state is OutputState.STOPPED


@patch("chronoplay.output.Popen")
def test_health_detects_process_failure(
    mock_popen: MagicMock,
) -> None:
    """Health checks should detect a process that has exited."""
    process = MagicMock()
    process.poll.return_value = 1
    process.stderr = MagicMock()
    process.stderr.read.return_value = "unexpected termination"
    mock_popen.return_value = process

    output = FFmpegOutput(make_config())
    output.start("/media/program.mp4")

    assert output.health() is False
    assert output.state is OutputState.FAILED
    assert output.last_error == "unexpected termination"
    assert output.process is None


def test_output_config_is_immutable() -> None:
    """OutputConfig should be immutable after creation."""
    config = make_config()

    with pytest.raises(AttributeError):
        config.name = "changed"  # type: ignore[misc]


@patch("chronoplay.output.Popen")
def test_start_uses_configured_output_name_in_error(
    mock_popen: MagicMock,
) -> None:
    """Startup errors should identify the configured backend name."""
    mock_popen.side_effect = OSError("backend unavailable")

    output = FFmpegOutput(
        make_config(name="primary-channel"),
    )

    with pytest.raises(
        OutputError,
        match="primary-channel",
    ):
        output.start("/media/program.mp4")

    assert output.state is OutputState.FAILED
