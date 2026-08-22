"""Media output abstractions for ChronoPlay."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import os
from subprocess import DEVNULL, PIPE, Popen, TimeoutExpired
from threading import RLock
from typing import Mapping, Protocol


class OutputError(RuntimeError):
    """Base exception for media output failures."""


class OutputConfigurationError(OutputError, ValueError):
    """Raised when an output configuration is invalid."""


class OutputState(str, Enum):
    """Lifecycle states for a media output."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """Configuration for a process-backed media output."""

    command: tuple[str, ...]
    name: str = "ffmpeg"
    environment: Mapping[str, str] = field(default_factory=dict)
    working_directory: str | None = None

    def __post_init__(self) -> None:
        if not self.command or not all(str(part).strip() for part in self.command):
            raise OutputConfigurationError("Output command cannot be empty.")
        if not self.name.strip():
            raise OutputConfigurationError("Output name cannot be empty.")


class MediaOutput(Protocol):
    """Protocol implemented by media output backends."""

    @property
    def state(self) -> OutputState:
        """Return the current output state."""

    def start(self, media_path: str) -> None:
        """Start output for a media asset."""

    def stop(self) -> None:
        """Stop the active output."""

    def health(self) -> bool:
        """Return whether the output is currently healthy."""


class FFmpegOutput:
    """Process-backed FFmpeg media output adapter.

    The configured command is appended with the media path. This keeps the
    adapter independent of a particular destination such as a file, UDP,
    SRT, RTMP, or hardware output supported by the installed FFmpeg build.
    """

    def __init__(self, config: OutputConfig) -> None:
        self.config = config
        self._process: Popen[str] | None = None
        self._state = OutputState.STOPPED
        self._lock = RLock()
        self._last_error: str | None = None

    @property
    def state(self) -> OutputState:
        """Return the current output state."""
        with self._lock:
            return self._state

    @property
    def last_error(self) -> str | None:
        """Return the most recent backend error, if any."""
        with self._lock:
            return self._last_error

    @property
    def process(self) -> Popen[str] | None:
        """Return the active process for supervision or testing."""
        with self._lock:
            return self._process

    def start(self, media_path: str) -> None:
        """Start FFmpeg output for ``media_path``."""
        if not media_path.strip():
            raise OutputConfigurationError("Media path cannot be empty.")

        with self._lock:
            if self._process is not None and self._process.poll() is None:
                raise OutputError("FFmpeg output is already running.")

            self._state = OutputState.STARTING
            self._last_error = None
            command = [*self.config.command, media_path]
            environment = None
            if self.config.environment:
                environment = {**os.environ, **self.config.environment}

            try:
                self._process = Popen(
                    command,
                    cwd=self.config.working_directory,
                    env=environment,
                    stdout=DEVNULL,
                    stderr=PIPE,
                    text=True,
                )
            except OSError as exc:
                self._process = None
                self._state = OutputState.FAILED
                self._last_error = str(exc)
                raise OutputError(
                    f"Unable to start output backend {self.config.name!r}."
                ) from exc

            self._state = OutputState.RUNNING

    def stop(self) -> None:
        """Stop the active FFmpeg process gracefully, then force termination."""
        with self._lock:
            process = self._process
            if process is None:
                self._state = OutputState.STOPPED
                return

            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

            if process.returncode not in (0, None):
                self._state = OutputState.FAILED
                self._last_error = self._read_stderr(process)
            else:
                self._state = OutputState.STOPPED

            self._process = None

    def health(self) -> bool:
        """Return true while the FFmpeg process is alive."""
        with self._lock:
            if self._process is None:
                return False

            if self._process.poll() is None:
                return True

            self._state = OutputState.FAILED
            self._last_error = self._read_stderr(self._process)
            self._process = None
            return False

    @staticmethod
    def _read_stderr(process: Popen[str]) -> str:
        if process.stderr is None:
            return ""
        try:
            return process.stderr.read().strip()
        except (OSError, ValueError):
            return ""
