from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from chronoplay.models import (
    UTC,
    Channel,
    MediaItem,
    ModelValidationError,
    ScheduleEntry,
    PlayoutAction,
    PlayoutCommand,
)


def make_media(
    *,
    path: str = "media/program.mp4",
    media_id: str = "media-001",
    duration: timedelta | None = timedelta(minutes=30),
    title: str | None = "Test Program",
) -> MediaItem:
    """Create a valid media item for tests."""
    return MediaItem(
        path=Path(path),
        media_id=media_id,
        duration=duration,
        title=title,
    )


def make_start() -> datetime:
    """Return a stable timezone-aware test timestamp."""
    return datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


def test_media_item_accepts_valid_values() -> None:
    """MediaItem should accept a valid media definition."""
    media = make_media()

    assert media.path == Path("media/program.mp4")
    assert media.media_id == "media-001"
    assert media.title == "Test Program"
    assert media.duration == timedelta(minutes=30)


def test_media_item_generates_id_when_omitted() -> None:
    """MediaItem should generate a non-empty identifier."""
    media = make_media(media_id="generated")

    assert media.media_id == "generated"


def test_media_item_rejects_empty_id() -> None:
    """MediaItem should reject an empty identifier."""
    with pytest.raises(
        ModelValidationError,
        match="media_id cannot be empty",
    ):
        make_media(media_id="   ")


def test_media_item_rejects_negative_duration() -> None:
    """MediaItem should reject negative durations."""
    with pytest.raises(
        ModelValidationError,
        match="Media duration cannot be negative",
    ):
        make_media(duration=timedelta(seconds=-1))


def test_media_item_accepts_zero_duration() -> None:
    """MediaItem should permit a zero duration."""
    media = make_media(duration=timedelta(0))

    assert media.duration == timedelta(0)


def test_media_item_rejects_empty_title() -> None:
    """MediaItem should reject an empty title."""
    with pytest.raises(
        ModelValidationError,
        match="Media title cannot be empty",
    ):
        make_media(title="   ")


def test_media_item_allows_missing_title() -> None:
    """MediaItem should allow a missing title."""
    media = make_media(title=None)

    assert media.title is None


def test_media_item_normalizes_path() -> None:
    """MediaItem should normalize its path to a Path object."""
    media = MediaItem(
        path="media/program.mp4",
        media_id="media-001",
    )

    assert isinstance(media.path, Path)
    assert media.path == Path("media/program.mp4")


def test_media_item_copies_metadata() -> None:
    """MediaItem should isolate its metadata from the input mapping."""
    metadata = {"genre": "news"}
    media = make_media()
    media_with_metadata = MediaItem(
        path=media.path,
        media_id=media.media_id,
        metadata=metadata,
    )

    metadata["genre"] = "sports"

    assert media_with_metadata.metadata["genre"] == "news"


def test_schedule_entry_accepts_valid_values() -> None:
    """ScheduleEntry should accept a valid media and start time."""
    media = make_media()
    entry = ScheduleEntry(
        media=media,
        start=make_start(),
        entry_id="entry-001",
    )

    assert entry.media == media
    assert entry.start == make_start()
    assert entry.entry_id == "entry-001"
    assert entry.enabled is True


def test_schedule_entry_normalizes_start_to_utc() -> None:
    """ScheduleEntry should normalize timezone-aware starts to UTC."""
    dhaka = timezone(timedelta(hours=6))
    start = datetime(2026, 8, 21, 18, 0, tzinfo=dhaka)

    entry = ScheduleEntry(
        media=make_media(),
        start=start,
    )

    assert entry.start == make_start()
    assert entry.start.tzinfo == UTC


def test_schedule_entry_rejects_naive_start() -> None:
    """ScheduleEntry should reject a naive start time."""
    with pytest.raises(
        ModelValidationError,
        match="start must be timezone-aware",
    ):
        ScheduleEntry(
            media=make_media(),
            start=datetime(2026, 8, 21, 12, 0),
        )


def test_schedule_entry_rejects_invalid_media() -> None:
    """ScheduleEntry should require a MediaItem."""
    with pytest.raises(
        ModelValidationError,
        match="media must be a MediaItem",
    ):
        ScheduleEntry(
            media="program.mp4",  # type: ignore[arg-type]
            start=make_start(),
        )


def test_schedule_entry_rejects_empty_id() -> None:
    """ScheduleEntry should reject an empty identifier."""
    with pytest.raises(
        ModelValidationError,
        match="entry_id cannot be empty",
    ):
        ScheduleEntry(
            media=make_media(),
            start=make_start(),
            entry_id="   ",
        )


def test_schedule_entry_rejects_negative_duration() -> None:
    """ScheduleEntry should reject negative durations."""
    with pytest.raises(
        ModelValidationError,
        match="Schedule duration cannot be negative",
    ):
        ScheduleEntry(
            media=make_media(),
            start=make_start(),
            duration=timedelta(seconds=-1),
        )


def test_schedule_entry_end_uses_entry_duration() -> None:
    """ScheduleEntry should prefer its own duration for its end time."""
    entry = ScheduleEntry(
        media=make_media(duration=timedelta(minutes=30)),
        start=make_start(),
        duration=timedelta(minutes=10),
    )

    assert entry.end == make_start() + timedelta(minutes=10)


def test_schedule_entry_end_falls_back_to_media_duration() -> None:
    """ScheduleEntry should use media duration when its own is absent."""
    entry = ScheduleEntry(
        media=make_media(duration=timedelta(minutes=30)),
        start=make_start(),
    )

    assert entry.end == make_start() + timedelta(minutes=30)


def test_schedule_entry_end_is_none_without_duration() -> None:
    """ScheduleEntry should have no end when neither duration is available."""
    entry = ScheduleEntry(
        media=make_media(duration=None),
        start=make_start(),
    )

    assert entry.end is None


def test_schedule_entry_metadata_is_copied() -> None:
    """ScheduleEntry should isolate its metadata from the input mapping."""
    metadata = {"category": "news"}
    entry = ScheduleEntry(
        media=make_media(),
        start=make_start(),
        metadata=metadata,
    )

    metadata["category"] = "sports"

    assert entry.metadata["category"] == "news"


def test_channel_accepts_valid_values() -> None:
    """Channel should accept valid schedule entries."""
    entry = ScheduleEntry(
        media=make_media(),
        start=make_start(),
    )
    channel = Channel(
        name="Main Channel",
        channel_id="channel-001",
        entries=(entry,),
    )

    assert channel.name == "Main Channel"
    assert channel.channel_id == "channel-001"
    assert channel.timezone == "UTC"
    assert channel.enabled is True
    assert channel.entries == (entry,)


def test_channel_converts_entries_to_tuple() -> None:
    """Channel should store entries as an immutable tuple."""
    entry = ScheduleEntry(
        media=make_media(),
        start=make_start(),
    )

    channel = Channel(
        name="Main Channel",
        entries=[entry],
    )

    assert isinstance(channel.entries, tuple)
    assert channel.entries == (entry,)


def test_channel_rejects_empty_name() -> None:
    """Channel should reject an empty name."""
    with pytest.raises(
        ModelValidationError,
        match="name cannot be empty",
    ):
        Channel(name="   ")


def test_channel_rejects_empty_id() -> None:
    """Channel should reject an empty identifier."""
    with pytest.raises(
        ModelValidationError,
        match="channel_id cannot be empty",
    ):
        Channel(
            name="Main Channel",
            channel_id="   ",
        )


def test_channel_rejects_empty_timezone() -> None:
    """Channel should reject an empty timezone identifier."""
    with pytest.raises(
        ModelValidationError,
        match="timezone cannot be empty",
    ):
        Channel(
            name="Main Channel",
            timezone="   ",
        )


def test_channel_rejects_invalid_entries() -> None:
    """Channel should only accept ScheduleEntry objects."""
    with pytest.raises(
        ModelValidationError,
        match="Channel entries must contain only ScheduleEntry objects",
    ):
        Channel(
            name="Main Channel",
            entries=("invalid",),  # type: ignore[arg-type]
        )


def test_channel_defaults_to_no_entries() -> None:
    """Channel should start with an empty schedule."""
    channel = Channel(name="Main Channel")

    assert channel.entries == ()


def test_channel_metadata_is_copied() -> None:
    """Channel should isolate metadata from the input mapping."""
    metadata = {"region": "BD"}
    channel = Channel(
        name="Main Channel",
        metadata=metadata,
    )

    metadata["region"] = "US"

    assert channel.metadata["region"] == "BD"


@pytest.mark.parametrize(
    ("action", "value"),
    [
        (PlayoutAction.PLAY, "play"),
        (PlayoutAction.STOP, "stop"),
        (PlayoutAction.PAUSE, "pause"),
        (PlayoutAction.RESUME, "resume"),
        (PlayoutAction.SWITCH, "switch"),
    ],
)
def test_playout_action_values(
    action: PlayoutAction,
    value: str,
) -> None:
    """PlayoutAction values should remain stable strings."""
    assert action.value == value
    assert str(action.value) == value


def test_playout_command_accepts_play_with_media() -> None:
    """A PLAY command should require and accept media."""
    media = make_media()
    command = PlayoutCommand(
        action=PlayoutAction.PLAY,
        media=media,
        channel_id="channel-001",
    )

    assert command.action is PlayoutAction.PLAY
    assert command.media == media
    assert command.channel_id == "channel-001"


def test_playout_command_rejects_play_without_media() -> None:
    """A PLAY command should require a media item."""
    with pytest.raises(
        ModelValidationError,
        match="PLAY commands require a media item",
    ):
        PlayoutCommand(action=PlayoutAction.PLAY)


@pytest.mark.parametrize(
    "action",
    [
        PlayoutAction.STOP,
        PlayoutAction.PAUSE,
        PlayoutAction.RESUME,
        PlayoutAction.SWITCH,
    ],
)
def test_non_play_commands_can_omit_media(
    action: PlayoutAction,
) -> None:
    """Non-PLAY commands should not require media."""
    command = PlayoutCommand(action=action)

    assert command.media is None


def test_playout_command_rejects_empty_id() -> None:
    """PlayoutCommand should reject an empty identifier."""
    with pytest.raises(
        ModelValidationError,
        match="command_id cannot be empty",
    ):
        PlayoutCommand(
            action=PlayoutAction.STOP,
            command_id="   ",
        )


def test_playout_command_rejects_empty_channel_id() -> None:
    """PlayoutCommand should reject an empty channel identifier."""
    with pytest.raises(
        ModelValidationError,
        match="channel_id cannot be empty",
    ):
        PlayoutCommand(
            action=PlayoutAction.STOP,
            channel_id="   ",
        )


def test_playout_command_normalizes_scheduled_time() -> None:
    """PlayoutCommand should normalize scheduled timestamps to UTC."""
    dhaka = timezone(timedelta(hours=6))
    scheduled_at = datetime(2026, 8, 21, 18, 0, tzinfo=dhaka)

    command = PlayoutCommand(
        action=PlayoutAction.STOP,
        scheduled_at=scheduled_at,
    )

    assert command.scheduled_at == make_start()
    assert command.scheduled_at.tzinfo == UTC


def test_playout_command_rejects_naive_scheduled_time() -> None:
    """PlayoutCommand should reject a naive scheduled timestamp."""
    with pytest.raises(
        ModelValidationError,
        match="scheduled_at must be timezone-aware",
    ):
        PlayoutCommand(
            action=PlayoutAction.STOP,
            scheduled_at=datetime(2026, 8, 21, 12, 0),
        )


def test_playout_command_metadata_is_copied() -> None:
    """PlayoutCommand should isolate metadata from the input mapping."""
    metadata = {"reason": "scheduled"}
    command = PlayoutCommand(
        action=PlayoutAction.STOP,
        metadata=metadata,
    )

    metadata["reason"] = "manual"

    assert command.metadata["reason"] == "scheduled"


def test_models_are_immutable() -> None:
    """Core domain models should reject direct field mutation."""
    media = make_media()

    with pytest.raises(AttributeError):
        media.media_id = "changed"  # type: ignore[misc]


def test_generated_identifiers_are_unique() -> None:
    """Automatically generated identifiers should not collide."""
    first = make_media(media_id="media-001")
    second = MediaItem(path=Path("media/other.mp4"))

    assert first.media_id != second.media_id
