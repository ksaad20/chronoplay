from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when ChronoPlay configuration is invalid."""


def _validate_text(value: str, field_name: str) -> str:
    """Validate a required text configuration value."""
    if not value.strip():
        raise ConfigurationError(f"{field_name} cannot be empty.")

    return value


def _validate_positive(value: float, field_name: str) -> float:
    """Validate a positive numeric configuration value."""
    if value <= 0:
        raise ConfigurationError(f"{field_name} must be greater than zero.")

    return value


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Configure application logging behavior."""

    level: str = "INFO"
    file: Path | None = None

    def __post_init__(self) -> None:
        """Validate logging configuration."""
        level = _validate_text(self.level, "level").upper()

        allowed_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if level not in allowed_levels:
            raise ConfigurationError(f"Unsupported logging level: {self.level}")

        object.__setattr__(self, "level", level)

        if self.file is not None:
            object.__setattr__(self, "file", Path(self.file))


@dataclass(frozen=True, slots=True)
class PlayoutConfig:
    """Configure scheduler and playout timing behavior."""

    poll_interval: float = 0.25
    startup_grace_period: float = 5.0
    late_event_threshold: float = 1.0

    def __post_init__(self) -> None:
        """Validate playout timing configuration."""
        _validate_positive(self.poll_interval, "poll_interval")

        if self.startup_grace_period < 0:
            raise ConfigurationError("startup_grace_period cannot be negative.")

        if self.late_event_threshold < 0:
            raise ConfigurationError("late_event_threshold cannot be negative.")


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    """Configure a ChronoPlay broadcast channel."""

    name: str
    channel_id: str = "main"
    timezone: str = "UTC"
    media_root: Path = Path("media")
    schedule_file: Path = Path("schedule.yaml")
    enabled: bool = True
    emergency_media: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate channel configuration."""
        _validate_text(self.name, "name")
        _validate_text(self.channel_id, "channel_id")
        _validate_text(self.timezone, "timezone")

        object.__setattr__(self, "media_root", Path(self.media_root))
        object.__setattr__(
            self,
            "schedule_file",
            Path(self.schedule_file),
        )

        if self.emergency_media is not None:
            object.__setattr__(
                self,
                "emergency_media",
                Path(self.emergency_media),
            )

        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class ChronoPlayConfig:
    """Top-level configuration for a ChronoPlay instance."""

    channel: ChannelConfig
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    playout: PlayoutConfig = field(default_factory=PlayoutConfig)
    application_name: str = "ChronoPlay"
    version: str = "0.0.1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the complete ChronoPlay configuration."""
        _validate_text(self.application_name, "application_name")
        _validate_text(self.version, "version")

        if not isinstance(self.channel, ChannelConfig):
            raise ConfigurationError("channel must be a ChannelConfig.")

        if not isinstance(self.logging, LoggingConfig):
            raise ConfigurationError("logging must be a LoggingConfig.")

        if not isinstance(self.playout, PlayoutConfig):
            raise ConfigurationError("playout must be a PlayoutConfig.")

        object.__setattr__(self, "metadata", dict(self.metadata))
