from __future__ import annotations

import subprocess

import pytest

from chronoplay.output import (
    FFmpegOutput,
    OutputConfig,
    OutputConfigurationError,
    OutputState,
)


def test_output_config_rejects_empty_command() -> None:
    with pytest.raises(OutputConfigurationError):
        OutputConfig(command=())


def test_output_config_rejects_blank_name() -> None:
    with pytest.raises(OutputConfigurationError):
        OutputConfig(command=("ffmpeg",), name=" ")


def test_ffmpeg_output_starts_and_reports_health(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeProcess:
        returncode = None
        stderr = None

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return 0

    captured: dict[str, object] = {}

    def fake_popen(
        command: list[str],
        **kwargs: object,
    ) -> FakeProcess:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    output = FFmpegOutput(
        OutputConfig(command=("ffmpeg", "-re", "-i")),
    )

    output.start("/media/program.mp4")

    assert captured["command"] == [
        "ffmpeg",
        "-re",
        "-i",
        "/media/program.mp4",
    ]
    assert output.state is OutputState.RUNNING
    assert output.health() is True

    output.stop()

    assert output.state is OutputState.STOPPED


def test_ffmpeg_output_rejects_empty_media_path() -> None:
    output = FFmpegOutput(OutputConfig(command=("ffmpeg",)))

    with pytest.raises(OutputConfigurationError):
        output.start("")


def test_ffmpeg_output_rejects_duplicate_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        returncode = None
        stderr = None

        def poll(self) -> None:
            return None

    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: FakeProcess(),
    )

    output = FFmpegOutput(OutputConfig(command=("ffmpeg",)))
    output.start("/media/program.mp4")

    with pytest.raises(RuntimeError, match="already running"):
        output.start("/media/second.mp4")

    output.stop()


def test_ffmpeg_output_health_detects_process_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        returncode = 1
        stderr = None

        def poll(self) -> int:
            return 1

    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: FakeProcess(),
    )

    output = FFmpegOutput(OutputConfig(command=("ffmpeg",)))
    output.start("/media/program.mp4")

    assert output.health() is False
    assert output.state is OutputState.FAILED
    assert output.process is None


def test_ffmpeg_output_start_failure_sets_failed_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_popen(*args: object, **kwargs: object) -> None:
        raise OSError("ffmpeg not found")

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    output = FFmpegOutput(OutputConfig(command=("ffmpeg",)))

    with pytest.raises(RuntimeError, match="Unable to start output"):
        output.start("/media/program.mp4")

    assert output.state is OutputState.FAILED
    assert output.last_error == "ffmpeg not found"


def test_ffmpeg_output_stop_without_process_is_safe() -> None:
    output = FFmpegOutput(OutputConfig(command=("ffmpeg",)))

    output.stop()

    assert output.state is OutputState.STOPPED


def test_ffmpeg_output_environment_is_passed_to_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeProcess:
        returncode = None
        stderr = None

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return 0

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    output = FFmpegOutput(
        OutputConfig(
            command=("ffmpeg",),
            environment={"CHRONOPLAY_OUTPUT": "test"},
        ),
    )

    output.start("/media/program.mp4")

    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["env"] == {"CHRONOPLAY_OUTPUT": "test"}

    output.stop()
