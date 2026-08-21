from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

UTC = timezone.utc


class ModelValidationError(ValueError):
    """Raised when a ChronoPlay domain model is invalid."""


class PlayoutAction(StrEnum):
    """Actions that the playout engine may perform."""

    PLAY = "play"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    SWITCH = "switch"


def _normalize_datetime(value: datetime, field_name: str) -> datetime:
    """Validate and normalize a datetime to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ModelValidationError(f"{field_name} must be timezone-aware.")

    return value.astimezone(UTC)


def _validate_identifier(value: str, field_name: str) -> str:
    """Validate and return a non-empty identifier."""
    if not value.strip():
        raise ModelValidationError(f"{field_name} cannot be empty.")

    return value


@dataclass(frozen=True, slots=True)
class MediaItem:
    """Describe a media asset that can be used by the playout engine."""

    path: Path
    media_id: str = field(default_factory=lambda: str(uuid4()))
    title: str | None = None
    duration: timedelta | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the media item."""
        _validate_identifier(self.media_id, "media_id")

        if self.duration is not None and self.duration < timedelta(0):
            raise ModelValidationError("Media duration cannot be negative.")

        if self.title is not None and not self.title.strip():
            raise ModelValidationError("Media title cannot be empty.")

        object.__setattr__(self, "path", Path(self.path))

        if not self.path.as_posix().strip():
            raise ModelValidationError("Media path cannot be empty.")

        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    """Associate a media item with an absolute broadcast start time."""

    media: MediaItem
    start: datetime
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    duration: timedelta | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize the schedule entry."""
        _validate_identifier(self.entry_id, "entry_id")

        if not isinstance(self.media, MediaItem):
            raise ModelValidationError("media must be a MediaItem.")

        normalized_start = _normalize_datetime(self.start, "start")
        object.__setattr__(self, "start", normalized_start)

        if self.duration is not None and self.duration < timedelta(0):
            raise ModelValidationError("Schedule duration cannot be negative.")

        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def end(self) -> datetime | None:
        """Return the expected end time when a duration is available."""
        duration = self.duration or self.media.duration

        if duration is None:
            return None

        return self.start + duration


@dataclass(frozen=True, slots=True)
class Channel:
    """Describe a broadcast channel and its scheduled programming."""

    name: str
    channel_id: str = field(default_factory=lambda: str(uuid4()))
    timezone: str = "UTC"
    enabled: bool = True
    entries: tuple[ScheduleEntry, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the channel definition."""
        _validate_identifier(self.name, "name")
        _validate_identifier(self.channel_id, "channel_id")
        _validate_identifier(self.timezone, "timezone")

        if not isinstance(self.entries, tuple):
            object.__setattr__(self, "entries", tuple(self.entries))

        if not all(isinstance(entry, ScheduleEntry) for entry in self.entries):
            raise ModelValidationError(
                "Channel entries must contain only ScheduleEntry objects."
            )

        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class PlayoutCommand:
    """Describe an action to be performed by the playout engine."""

    action: PlayoutAction
    media: MediaItem | None = None
    channel_id: str | None = None
    scheduled_at: datetime | None = None
    command_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize the playout command."""
        _validate_identifier(self.command_id, "command_id")

        if self.channel_id is not None:
            _validate_identifier(self.channel_id, "channel_id")

        if self.scheduled_at is not None:
            object.__setattr__(
                self,
                "scheduled_at",
                _normalize_datetime(self.scheduled_at, "scheduled_at"),
            )

        if self.action == PlayoutAction.PLAY and self.media is None:
            raise ModelValidationError(
                "PLAY commands require a media item."
            )

        object.__setattr__(self, "metadata", dict(self.metadata))
