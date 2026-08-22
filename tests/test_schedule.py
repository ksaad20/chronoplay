from datetime import datetime, timedelta, timezone

import pytest
import yaml

from chronoplay.config import ChannelConfig
from chronoplay.schedule import (
    ScheduleFileError,
    ScheduleParseError,
    _parse_datetime,
    _parse_duration,
    _require_mapping,
    _require_text,
    load_schedule,
)


@pytest.fixture
def channel_config(tmp_path):
    return ChannelConfig(
        name="Test Channel",
        channel_id="test-channel",
        timezone="UTC",
        media_root=tmp_path,
        enabled=True,
        metadata={},
    )


def write_schedule(tmp_path, content):
    path = tmp_path / "schedule.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_require_mapping_accepts_mapping():
    value = {"schedule": []}

    assert _require_mapping(value, "test") == value


@pytest.mark.parametrize("value", [None, [], "text", 123])
def test_require_mapping_rejects_non_mapping(value):
    with pytest.raises(ScheduleParseError, match="must be a mapping"):
        _require_mapping(value, "test")


def test_require_text_accepts_and_strips_string():
    assert _require_text("  hello  ", "name") == "hello"


@pytest.mark.parametrize("value", [None, "", "   ", 123, [], {}])
def test_require_text_rejects_invalid_values(value):
    with pytest.raises(ScheduleParseError, match="must be a non-empty string"):
        _require_text(value, "name")


def test_parse_datetime_accepts_timezone_aware_value():
    result = _parse_datetime(
        "2026-08-22T12:00:00+00:00",
        "start",
    )

    assert result == datetime(
        2026,
        8,
        22,
        12,
        0,
        tzinfo=timezone.utc,
    )


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not-a-date",
        "2026-08-22T12:00:00",
    ],
)
def test_parse_datetime_rejects_invalid_values(value):
    with pytest.raises(ScheduleParseError):
        _parse_datetime(value, "start")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (30, timedelta(seconds=30)),
        (30.5, timedelta(seconds=30.5)),
        ("00:01:30", timedelta(minutes=1, seconds=30)),
        ("01:02:03", timedelta(hours=1, minutes=2, seconds=3)),
        ("00:00:00.5", timedelta(seconds=0.5)),
    ],
)
def test_parse_duration_accepts_valid_values(value, expected):
    assert _parse_duration(value, "duration") == expected


@pytest.mark.parametrize(
    "value",
    [
        -1,
        -0.5,
        "",
        "   ",
        "1:2",
        "1:2:3:4",
        "abc:def:ghi",
        "-1:00:00",
        "00:-1:00",
        "00:00:-1",
        "00:60:00",
        "00:00:60",
        [],
        {},
    ],
)
def test_parse_duration_rejects_invalid_values(value):
    with pytest.raises(ScheduleParseError):
        _parse_duration(value, "duration")


def test_load_schedule_loads_and_sorts_enabled_entries(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: second
    start: "2026-08-22T13:00:00+00:00"
    media:
      path: second.mp4
      title: Second
      duration: "00:02:00"

  - id: first
    start: "2026-08-22T12:00:00+00:00"
    media:
      path: first.mp4
      title: First
      duration: 60

  - id: disabled
    start: "2026-08-22T11:00:00+00:00"
    enabled: false
    media:
      path: disabled.mp4
"""
    )

    channel = load_schedule(path, channel_config)

    assert channel.name == "Test Channel"
    assert channel.channel_id == "test-channel"
    assert channel.enabled is True
    assert len(channel.entries) == 2
    assert [entry.entry_id for entry in channel.entries] == [
        "first",
        "second",
    ]

    assert channel.entries[0].media.path == tmp_path / "first.mp4"
    assert channel.entries[1].media.path == tmp_path / "second.mp4"


def test_load_schedule_uses_media_id_when_supplied(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: entry-1
    start: "2026-08-22T12:00:00+00:00"
    media:
      id: custom-media
      path: program.mp4
"""
    )

    channel = load_schedule(path, channel_config)

    assert channel.entries[0].media.media_id == "custom-media"


def test_load_schedule_uses_media_path_as_default_media_id(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: entry-1
    start: "2026-08-22T12:00:00+00:00"
    media:
      path: program.mp4
"""
    )

    channel = load_schedule(path, channel_config)

    assert channel.entries[0].media.media_id == "program.mp4"


def test_load_schedule_preserves_metadata(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: entry-1
    start: "2026-08-22T12:00:00+00:00"
    metadata:
      category: news
      priority: 10
    media:
      path: program.mp4
      metadata:
        language: en
"""
    )

    channel = load_schedule(path, channel_config)

    assert channel.entries[0].metadata == {
        "category": "news",
        "priority": 10,
    }
    assert channel.entries[0].media.metadata == {
        "language": "en",
    }


def test_load_schedule_rejects_missing_file(
    tmp_path,
    channel_config,
):
    missing = tmp_path / "missing.yaml"

    with pytest.raises(ScheduleFileError, match="Unable to read schedule file"):
        load_schedule(missing, channel_config)


def test_load_schedule_rejects_invalid_yaml(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: broken
    media: [
"""
    )

    with pytest.raises(ScheduleParseError, match="Unable to parse YAML schedule"):
        load_schedule(path, channel_config)


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        "schedule: null",
        "schedule: {}",
        "schedule: text",
    ],
)
def test_load_schedule_rejects_invalid_root_or_schedule(
    tmp_path,
    channel_config,
    content,
):
    path = write_schedule(tmp_path, content)

    with pytest.raises(ScheduleParseError):
        load_schedule(path, channel_config)


def test_load_schedule_requires_schedule_field(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        "channel: test\n",
    )

    with pytest.raises(
        ScheduleParseError,
        match="must contain a 'schedule' field",
    ):
        load_schedule(path, channel_config)


def test_load_schedule_rejects_duplicate_entry_ids(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: duplicate
    start: "2026-08-22T12:00:00+00:00"
    media:
      path: first.mp4

  - id: duplicate
    start: "2026-08-22T13:00:00+00:00"
    media:
      path: second.mp4
"""
    )

    with pytest.raises(
        ScheduleParseError,
        match="Duplicate schedule entry ID",
    ):
        load_schedule(path, channel_config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", ""),
        ("start", "not-a-date"),
    ],
)
def test_load_schedule_rejects_invalid_entry_fields(
    tmp_path,
    channel_config,
    field,
    value,
):
    entry = {
        "id": "entry-1",
        "start": "2026-08-22T12:00:00+00:00",
        "media": {"path": "program.mp4"},
    }
    entry[field] = value

    path = write_schedule(
        tmp_path,
        yaml.safe_dump({"schedule": [entry]}),
    )

    with pytest.raises(ScheduleParseError):
        load_schedule(path, channel_config)


@pytest.mark.parametrize(
    "media",
    [
        None,
        {},
        {"path": ""},
        {"path": 123},
        {"path": "program.mp4", "id": ""},
        {"path": "program.mp4", "title": 123},
        {"path": "program.mp4", "metadata": []},
        {"path": "program.mp4", "duration": "invalid"},
    ],
)
def test_load_schedule_rejects_invalid_media(
    tmp_path,
    channel_config,
    media,
):
    path = write_schedule(
        tmp_path,
        yaml.safe_dump(
            {
                "schedule": [
                    {
                        "id": "entry-1",
                        "start": "2026-08-22T12:00:00+00:00",
                        "media": media,
                    }
                ]
            }
        ),
    )

    with pytest.raises(ScheduleParseError):
        load_schedule(path, channel_config)


@pytest.mark.parametrize("enabled", [None, "true", 1, 0, []])
def test_load_schedule_rejects_non_boolean_enabled(
    tmp_path,
    channel_config,
    enabled,
):
    path = write_schedule(
        tmp_path,
        yaml.safe_dump(
            {
                "schedule": [
                    {
                        "id": "entry-1",
                        "start": "2026-08-22T12:00:00+00:00",
                        "enabled": enabled,
                        "media": {"path": "program.mp4"},
                    }
                ]
            }
        ),
    )

    with pytest.raises(ScheduleParseError, match="enabled must be boolean"):
        load_schedule(path, channel_config)


def test_load_schedule_rejects_non_mapping_entry(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        yaml.safe_dump({"schedule": ["not-a-mapping"]}),
    )

    with pytest.raises(ScheduleParseError, match="must be a mapping"):
        load_schedule(path, channel_config)


def test_load_schedule_rejects_non_mapping_entry_metadata(
    tmp_path,
    channel_config,
):
    path = write_schedule(
        tmp_path,
        """
schedule:
  - id: entry-1
    start: "2026-08-22T12:00:00+00:00"
    metadata: invalid
    media:
      path: program.mp4
"""
    )

    with pytest.raises(ScheduleParseError, match="metadata must be a mapping"):
        load_schedule(path, channel_config)
