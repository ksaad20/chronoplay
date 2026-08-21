from __future__ import annotations

from pathlib import Path

import pytest

from chronoplay.config import (
    ChannelConfig,
    ChronoPlayConfig,
    ConfigurationError,
    LoggingConfig,
    PlayoutConfig,
)


def test_logging_config_defaults() -> None:
    """LoggingConfig should provide production-safe defaults."""
    config = LoggingConfig()

    assert config.level == "INFO"
    assert config.file is None


@pytest.mark.parametrize(
    "level",
    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
)
def test_logging_config_accepts_valid_levels(level: str) -> None:
    """LoggingConfig should accept supported logging levels."""
    config = LoggingConfig(level=level)

    assert config.level == level


def test_logging_config_normalizes_level() -> None:
    """LoggingConfig should normalize lowercase levels."""
    config = LoggingConfig(level="warning")

    assert config.level == "WARNING"


def test_logging_config_rejects_empty_level() -> None:
    """LoggingConfig should reject an empty logging level."""
    with pytest.raises(
        ConfigurationError,
        match="level cannot be empty",
    ):
        LoggingConfig(level="   ")


def test_logging_config_rejects_unsupported_level() -> None:
    """LoggingConfig should reject unsupported logging levels."""
    with pytest.raises(
        ConfigurationError,
        match="Unsupported logging level",
    ):
        LoggingConfig(level="TRACE")


def test_logging_config_normalizes_file_path() -> None:
    """LoggingConfig should normalize file paths to Path objects."""
    config = LoggingConfig(file="logs/chronoplay.log")

    assert config.file == Path("logs/chronoplay.log")
    assert isinstance(config.file, Path)


def test_playout_config_defaults() -> None:
    """PlayoutConfig should provide deterministic defaults."""
    config = PlayoutConfig()

    assert config.poll_interval == 0.25
    assert config.startup_grace_period == 5.0
    assert config.late_event_threshold == 1.0


def test_playout_config_accepts_custom_values() -> None:
    """PlayoutConfig should accept valid timing values."""
    config = PlayoutConfig(
        poll_interval=0.5,
        startup_grace_period=10.0,
        late_event_threshold=2.0,
    )

    assert config.poll_interval == 0.5
    assert config.startup_grace_period == 10.0
    assert config.late_event_threshold == 2.0


def test_playout_config_rejects_non_positive_poll_interval() -> None:
    """PlayoutConfig should require a positive polling interval."""
    with pytest.raises(
        ConfigurationError,
        match="poll_interval must be greater than zero",
    ):
        PlayoutConfig(poll_interval=0)


def test_playout_config_rejects_negative_poll_interval() -> None:
    """PlayoutConfig should reject a negative polling interval."""
    with pytest.raises(
        ConfigurationError,
        match="poll_interval must be greater than zero",
    ):
        PlayoutConfig(poll_interval=-1)


def test_playout_config_rejects_negative_startup_grace_period() -> None:
    """PlayoutConfig should reject a negative startup grace period."""
    with pytest.raises(
        ConfigurationError,
        match="startup_grace_period cannot be negative",
    ):
        PlayoutConfig(startup_grace_period=-1)


def test_playout_config_rejects_negative_late_event_threshold() -> None:
    """PlayoutConfig should reject a negative late-event threshold."""
    with pytest.raises(
        ConfigurationError,
        match="late_event_threshold cannot be negative",
    ):
        PlayoutConfig(late_event_threshold=-1)


def test_channel_config_defaults() -> None:
    """ChannelConfig should provide useful channel defaults."""
    config = ChannelConfig(name="Main Channel")

    assert config.name == "Main Channel"
    assert config.channel_id == "main"
    assert config.timezone == "UTC"
    assert config.media_root == Path("media")
    assert config.schedule_file == Path("schedule.yaml")
    assert config.enabled is True
    assert config.emergency_media is None
    assert config.metadata == {}


def test_channel_config_accepts_custom_values() -> None:
    """ChannelConfig should accept valid custom settings."""
    config = ChannelConfig(
        name="News Channel",
        channel_id="news",
        timezone="Asia/Dhaka",
        media_root="content",
        schedule_file="config/news.yaml",
        enabled=False,
        emergency_media="fallback/emergency.mp4",
    )

    assert config.name == "News Channel"
    assert config.channel_id == "news"
    assert config.timezone == "Asia/Dhaka"
    assert config.media_root == Path("content")
    assert config.schedule_file == Path("config/news.yaml")
    assert config.enabled is False
    assert config.emergency_media == Path("fallback/emergency.mp4")


def test_channel_config_rejects_empty_name() -> None:
    """ChannelConfig should reject an empty channel name."""
    with pytest.raises(
        ConfigurationError,
        match="name cannot be empty",
    ):
        ChannelConfig(name="   ")


def test_channel_config_rejects_empty_channel_id() -> None:
    """ChannelConfig should reject an empty channel identifier."""
    with pytest.raises(
        ConfigurationError,
        match="channel_id cannot be empty",
    ):
        ChannelConfig(
            name="Main Channel",
            channel_id="   ",
        )


def test_channel_config_rejects_empty_timezone() -> None:
    """ChannelConfig should reject an empty timezone."""
    with pytest.raises(
        ConfigurationError,
        match="timezone cannot be empty",
    ):
        ChannelConfig(
            name="Main Channel",
            timezone="   ",
        )


def test_channel_config_copies_metadata() -> None:
    """ChannelConfig should isolate metadata from the source mapping."""
    metadata = {"region": "BD"}

    config = ChannelConfig(
        name="Main Channel",
        metadata=metadata,
    )

    metadata["region"] = "US"

    assert config.metadata["region"] == "BD"


def test_chronoplay_config_defaults() -> None:
    """ChronoPlayConfig should construct with validated defaults."""
    channel = ChannelConfig(name="Main Channel")
    config = ChronoPlayConfig(channel=channel)

    assert config.channel == channel
    assert config.logging == LoggingConfig()
    assert config.playout == PlayoutConfig()
    assert config.application_name == "ChronoPlay"
    assert config.version == "0.0.1"
    assert config.metadata == {}


def test_chronoplay_config_accepts_custom_components() -> None:
    """ChronoPlayConfig should accept custom configuration components."""
    channel = ChannelConfig(
        name="News Channel",
        channel_id="news",
    )
    logging = LoggingConfig(
        level="DEBUG",
        file="logs/news.log",
    )
    playout = PlayoutConfig(
        poll_interval=0.5,
        startup_grace_period=10.0,
        late_event_threshold=2.0,
    )

    config = ChronoPlayConfig(
        channel=channel,
        logging=logging,
        playout=playout,
        application_name="ChronoPlay News",
        version="0.0.1",
    )

    assert config.channel == channel
    assert config.logging == logging
    assert config.playout == playout
    assert config.application_name == "ChronoPlay News"
    assert config.version == "0.0.1"


def test_chronoplay_config_rejects_empty_application_name() -> None:
    """ChronoPlayConfig should reject an empty application name."""
    channel = ChannelConfig(name="Main Channel")

    with pytest.raises(
        ConfigurationError,
        match="application_name cannot be empty",
    ):
        ChronoPlayConfig(
            channel=channel,
            application_name="   ",
        )


def test_chronoplay_config_rejects_empty_version() -> None:
    """ChronoPlayConfig should reject an empty version."""
    channel = ChannelConfig(name="Main Channel")

    with pytest.raises(
        ConfigurationError,
        match="version cannot be empty",
    ):
        ChronoPlayConfig(
            channel=channel,
            version="   ",
        )


def test_chronoplay_config_rejects_invalid_channel() -> None:
    """ChronoPlayConfig should require a ChannelConfig."""
    with pytest.raises(
        ConfigurationError,
        match="channel must be a ChannelConfig",
    ):
        ChronoPlayConfig(
            channel="invalid",  # type: ignore[arg-type]
        )


def test_chronoplay_config_rejects_invalid_logging_config() -> None:
    """ChronoPlayConfig should require a LoggingConfig."""
    channel = ChannelConfig(name="Main Channel")

    with pytest.raises(
        ConfigurationError,
        match="logging must be a LoggingConfig",
    ):
        ChronoPlayConfig(
            channel=channel,
            logging="invalid",  # type: ignore[arg-type]
        )


def test_chronoplay_config_rejects_invalid_playout_config() -> None:
    """ChronoPlayConfig should require a PlayoutConfig."""
    channel = ChannelConfig(name="Main Channel")

    with pytest.raises(
        ConfigurationError,
        match="playout must be a PlayoutConfig",
    ):
        ChronoPlayConfig(
            channel=channel,
            playout="invalid",  # type: ignore[arg-type]
        )


def test_chronoplay_config_copies_metadata() -> None:
    """ChronoPlayConfig should isolate metadata from the source mapping."""
    metadata = {"deployment": "production"}
    channel = ChannelConfig(name="Main Channel")

    config = ChronoPlayConfig(
        channel=channel,
        metadata=metadata,
    )

    metadata["deployment"] = "development"

    assert config.metadata["deployment"] == "production"


def test_configuration_objects_are_immutable() -> None:
    """Configuration objects should reject direct field mutation."""
    config = ChannelConfig(name="Main Channel")

    with pytest.raises(AttributeError):
        config.name = "Changed Channel"  # type: ignore[misc]


def test_nested_configuration_objects_are_independent() -> None:
    """Default nested configuration objects should be valid independently."""
    first = ChronoPlayConfig(
        channel=ChannelConfig(name="Channel One"),
    )
    second = ChronoPlayConfig(
        channel=ChannelConfig(name="Channel Two"),
    )

    assert first.logging == second.logging
    assert first.playout == second.playout
    assert first.channel != second.channel
