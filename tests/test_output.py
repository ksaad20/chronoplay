from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from chronoplay.output import (
    OutputConfig,
    OutputError,
    OutputResult,
    OutputState,
    PlayoutOutput,
)


@dataclass
class FakeProcess:
    """Minimal process double for output lifecycle tests."""

    started: bool = False
    terminated: bool = False

    def start(self) -> None:
        """Mark the fake process as started."""
        self.started = True

    def terminate(self) -> None:
        """Mark the fake process as terminated."""
        self.terminated = True


def test_output_config_accepts_command() -> None:
    """OutputConfig should preserve the configured command."""
    config = OutputConfig(
        command=("ffmpeg", "-version"),
    )

    assert config.command == ("ffmpeg", "-version")


def test_output_config_accepts_environment() -> None:
    """OutputConfig should preserve environment variables."""
    config = OutputConfig(
        command=("ffmpeg",),
        environment={"CHRONOPLAY_OUTPUT": "test"},
    )

    assert config.environment == {"CHRONOPLAY_OUTPUT": "test"}


def test_output_config_defaults_environment_to_empty() -> None:
    """OutputConfig should provide an empty environment by default."""
    config = OutputConfig(
        command=("ffmpeg",),
    )

    assert config.environment == {}


def test_output_config_rejects_empty_command() -> None:
    """OutputConfig should reject an empty command."""
    with pytest.raises(
        ValueError,
        match="Output command cannot be empty",
    ):
        OutputConfig(command=())


def test_output_config_rejects_empty_command_argument() -> None:
    """OutputConfig should reject empty command arguments."""
    with pytest.raises(
        ValueError,
        match="Output command arguments cannot be empty",
    ):
        OutputConfig(command=("ffmpeg", ""))


def test_output_starts_stopped() -> None:
    """A new output should start in the stopped state."""
    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
    )

    assert output.state is OutputState.STOPPED
    assert output.result is None


def test_output_start_changes_state() -> None:
    """Starting an output should change its state to running."""
    process = FakeProcess()
    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
        process_factory=lambda _: process,
    )

    result = output.start()

    assert process.started is True
    assert output.state is OutputState.RUNNING
    assert isinstance(result, OutputResult)
    assert result.state is OutputState.RUNNING


def test_output_start_accepts_optional_program_argument() -> None:
    """start should accept an optional program identifier."""
    process = FakeProcess()
    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
        process_factory=lambda _: process,
    )

    result = output.start("/media/program.mp4")

    assert result.program == "/media/program.mp4"
    assert output.state is OutputState.RUNNING


def test_output_cannot_start_twice() -> None:
    """Starting an already-running output should raise OutputError."""
    process = FakeProcess()
    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
        process_factory=lambda _: process,
    )

    output.start()

    with pytest.raises(
        OutputError,
        match="already running",
    ):
        output.start()


def test_output_stop_changes_state() -> None:
    """Stopping a running output should return it to stopped."""
    process = FakeProcess()
    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
        process_factory=lambda _: process,
    )

    output.start()
    result = output.stop()

    assert process.terminated is True
    assert output.state is OutputState.STOPPED
    assert isinstance(result, OutputResult)
    assert result.state is OutputState.STOPPED


def test_output_stop_is_safe_when_stopped() -> None:
    """Stopping an inactive output should be safe."""
    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
    )

    result = output.stop()

    assert output.state is OutputState.STOPPED
    assert result.state is OutputState.STOPPED


def test_output_command_is_available() -> None:
    """The configured command should be exposed unchanged."""
    config = OutputConfig(
        command=("ffmpeg", "-re"),
    )
    output = PlayoutOutput(config)

    assert output.command == ("ffmpeg", "-re")


def test_output_environment_is_copied() -> None:
    """Output environment should not share mutable state with the caller."""
    environment = {"CHRONOPLAY_OUTPUT": "test"}
    output = PlayoutOutput(
        OutputConfig(
            command=("ffmpeg",),
            environment=environment,
        ),
    )

    environment["CHRONOPLAY_OUTPUT"] = "changed"

    assert output.environment == {"CHRONOPLAY_OUTPUT": "test"}


def test_output_result_contains_command() -> None:
    """OutputResult should report the configured command."""
    command = ("ffmpeg", "-re", "program.mp4")
    process = FakeProcess()
    output = PlayoutOutput(
        OutputConfig(command=command),
        process_factory=lambda _: process,
    )

    result = output.start()

    assert result.command == command


def test_output_process_failure_sets_error_state() -> None:
    """A process factory failure should put the output into an error state."""

    def failing_factory(_: Any) -> FakeProcess:
        raise RuntimeError("process failed")

    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
        process_factory=failing_factory,
    )

    with pytest.raises(
        OutputError,
        match="Failed to start output",
    ):
        output.start()

    assert output.state is OutputState.ERROR


def test_output_reset_recovers_error_state() -> None:
    """Reset should return an errored output to stopped."""
    def failing_factory(_: Any) -> FakeProcess:
        raise RuntimeError("process failed")

    output = PlayoutOutput(
        OutputConfig(command=("ffmpeg",)),
        process_factory=failing_factory,
    )

    with pytest.raises(OutputError):
        output.start()

    output.reset()

    assert output.state is OutputState.STOPPED
    assert output.result is None


def test_output_environment_is_available_to_process_factory() -> None:
    """The process factory should receive the configured environment."""
    received: dict[str, str] = {}
    process = FakeProcess()

    def factory(environment: dict[str, str]) -> FakeProcess:
        received.update(environment)
        return process

    output = PlayoutOutput(
        OutputConfig(
            command=("ffmpeg",),
            environment={"CHRONOPLAY_OUTPUT": "test"},
        ),
        process_factory=factory,
    )

    output.start()

    assert received == {"CHRONOPLAY_OUTPUT": "test"}
