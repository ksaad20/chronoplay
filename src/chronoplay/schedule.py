from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from chronoplay.config import ChannelConfig
from chronoplay.models import (
    Channel,
    MediaItem,
    ModelValidationError,
    ScheduleEntry,
)


class ScheduleError(ValueError):
    """Base exception for schedule loading and validation errors."""


class ScheduleParseError(ScheduleError):
    """Raised when a schedule cannot be parsed."""


class ScheduleFileError(ScheduleError):
    """Raised when a schedule file cannot be read."""


def _require_mapping(value: Any, context: str) -> dict[str, Any]:
    """Require a YAML value to be a mapping."""
    if not isinstance(value, dict):
        raise ScheduleParseError(f"{context} must be a mapping.")

    return value


def _require_text(value: Any, field_name: str) -> str:
    """Require a non-empty string value."""
    if not isinstance(value, str) or not value.strip():
        raise ScheduleParseError(f"{field_name} must be a non-empty string.")

    return value.strip()


def _parse_datetime(value: Any, field_name: str) -> datetime:
    """Parse a timezone-aware ISO-8601 datetime."""
    text = _require_text(value, field_name)

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ScheduleParseError(f"{field_name} must be a valid ISO-8601 datetime.") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ScheduleParseError(f"{field_name} must include timezone information.")

    return parsed


def _parse_duration(value: Any, field_name: str) -> timedelta | None:
    """Parse a duration expressed as seconds or HH:MM:SS."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        if value < 0:
            raise ScheduleParseError(f"{field_name} cannot be negative.")

        return timedelta(seconds=value)

    if not isinstance(value, str):
        raise ScheduleParseError(f"{field_name} must be seconds or HH:MM:SS.")

    text = value.strip()

    if not text:
        raise ScheduleParseError(f"{field_name} cannot be empty.")

    parts = text.split(":")

    if len(parts) != 3:
        raise ScheduleParseError(f"{field_name} must use HH:MM:SS format.")

    try:
        hours, minutes, seconds = (
            float(part) for part in parts
        )
    except ValueError as exc:
        raise ScheduleParseError(f"{field_name} must use HH:MM:SS format.") from exc

    if hours < 0 or minutes < 0 or seconds < 0:
        raise ScheduleParseError(f"{field_name} cannot be negative.")

    if minutes >= 60 or seconds >= 60:
        raise ScheduleParseError(f"{field_name} contains invalid minutes or seconds.")

    return timedelta(
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )


def _parse_media(
    value: Any,
    media_root: Path,
    entry_index: int,
) -> MediaItem:
    """Convert a schedule media definition into a MediaItem."""
    media_data = _require_mapping(
        value,
        f"schedule entry {entry_index} media",
    )

    media_path = _require_text(
        media_data.get("path"),
        f"schedule entry {entry_index} media.path",
    )

    media_id = media_data.get("id")

    if media_id is None:
        media_id = media_path

    media_id = _require_text(
        media_id,
        f"schedule entry {entry_index} media.id",
    )

    title = media_data.get("title")

    if title is not None:
        title = _require_text(
            title,
            f"schedule entry {entry_index} media.title",
        )

    duration = _parse_duration(
        media_data.get("duration"),
        f"schedule entry {entry_index} media.duration",
    )

    metadata = media_data.get("metadata", {})

    if not isinstance(metadata, dict):
        raise ScheduleParseError(f"schedule entry {entry_index} media.metadata must be a mapping.")

    path = Path(media_path)

    if not path.is_absolute():
        path = media_root / path

    try:
        return MediaItem(
            path=path,
            media_id=media_id,
            title=title,
            duration=duration,
            metadata=metadata,
        )
    except ModelValidationError as exc:
        raise ScheduleParseError(f"Invalid media in schedule entry {entry_index}: {exc}") from exc


def _parse_entry(
    value: Any,
    media_root: Path,
    entry_index: int,
) -> ScheduleEntry:
    """Convert a YAML schedule entry into a ScheduleEntry."""
    data = _require_mapping(
        value,
        f"schedule entry {entry_index}",
    )

    entry_id = _require_text(
        data.get("id"),
        f"schedule entry {entry_index} id",
    )

    start = _parse_datetime(
        data.get("start"),
        f"schedule entry {entry_index} start",
    )

    media = _parse_media(
        data.get("media"),
        media_root,
        entry_index,
    )

    duration = _parse_duration(
        data.get("duration"),
        f"schedule entry {entry_index} duration",
    )

    enabled = data.get("enabled", True)

    if not isinstance(enabled, bool):
        raise ScheduleParseError(f"schedule entry {entry_index} enabled must be boolean.")

    metadata = data.get("metadata", {})

    if not isinstance(metadata, dict):
        raise ScheduleParseError(f"schedule entry {entry_index} metadata must be a mapping.")

    try:
        return ScheduleEntry(
            media=media,
            start=start,
            entry_id=entry_id,
            duration=duration,
            enabled=enabled,
            metadata=metadata,
        )
    except ModelValidationError as exc:
        raise ScheduleParseError(f"Invalid schedule entry {entry_index}: {exc}") from exc


def load_schedule(
    path: str | Path,
    channel_config: ChannelConfig,
) -> Channel:
    """Load a YAML schedule and return a validated Channel.

    Parameters
    ----------
    path:
        Path to the YAML schedule file.
    channel_config:
        Configuration describing the target channel.

    Returns
    -------
    Channel
        Validated channel containing the schedule entries.

    Raises
    ------
    ScheduleFileError
        If the schedule file cannot be read.
    ScheduleParseError
        If the YAML or schedule structure is invalid.
    """
    schedule_path = Path(path)

    try:
        with schedule_path.open("r", encoding="utf-8") as file:
            document = yaml.safe_load(file)
    except OSError as exc:
        raise ScheduleFileError(f"Unable to read schedule file: {schedule_path}") from exc
    except yaml.YAMLError as exc:
        raise ScheduleParseError(f"Unable to parse YAML schedule: {schedule_path}") from exc

    root = _require_mapping(document, "schedule document")

    schedule_data = root.get("schedule")

    if schedule_data is None:
        raise ScheduleParseError("schedule document must contain a 'schedule' field.")

    if not isinstance(schedule_data, list):
        raise ScheduleParseError("schedule must be a list.")

    entries: list[ScheduleEntry] = []
    entry_ids: set[str] = set()

    for index, raw_entry in enumerate(schedule_data, start=1):
        entry = _parse_entry(
            raw_entry,
            channel_config.media_root,
            index,
        )

        if entry.entry_id in entry_ids:
            raise ScheduleParseError(f"Duplicate schedule entry ID: {entry.entry_id}")

        entry_ids.add(entry.entry_id)

        if entry.enabled:
            entries.append(entry)

    entries.sort(
        key=lambda item: (
            item.start,
            item.entry_id,
        )
    )

    return Channel(
        name=channel_config.name,
        channel_id=channel_config.channel_id,
        timezone=channel_config.timezone,
        enabled=channel_config.enabled,
        entries=tuple(entries),
        metadata=channel_config.metadata,
)
