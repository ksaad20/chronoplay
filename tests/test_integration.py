from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from chronoplay.media import MediaAsset
from chronoplay.output import FFmpegOutput, OutputConfig
from chronoplay.playout import PlayoutEngine, PlayoutState
from chronoplay.scheduler import ScheduleEvent, Scheduler

UTC = timezone.utc


def make_media() -> MediaAsset:
    """Create a minimal media asset for integration tests."""
    return MediaAsset(
        path="/media/program.mp4",
        duration=300,
    )


def make_event() -> ScheduleEvent:
    """Create a scheduled media event."""
    return ScheduleEvent(
        event_id="event-1",
        start=datetime(2026, 8, 22, 12, 0, tzinfo=UTC),
        duration=timedelta(minutes=5),
        payload=make_media(),
    )


def make_output() -> FFmpegOutput:
    """Create an FFmpeg output configured for testing."""
    return FFmpegOutput(
        OutputConfig(
            command=("ffmpeg",),
            environment={"CHRONOPLAY_OUTPUT": "test"},
        )
    )


def test_schedule_event_can_be_added_to_scheduler() -> None:
    """A valid schedule event should be accepted by the scheduler."""
    scheduler = Scheduler()
    event = make_event()

    scheduler.add(event)

    assert scheduler.get(event.event_id) == event


def test_scheduler_returns_event_in_start_order() -> None:
    """Scheduler should return events in chronological order."""
    scheduler = Scheduler()

    later = ScheduleEvent(
        event_id="event-2",
        start=datetime(2026, 8, 22, 13, 0, tzinfo=UTC),
        duration=timedelta(minutes=5),
        payload=make_media(),
    )
    earlier = make_event()

    scheduler.add(later)
    scheduler.add(earlier)

    events = scheduler.events()

    assert [event.event_id for event in events] == [
        "event-1",
        "event-2",
    ]


def test_playout_engine_accepts_scheduled_media() -> None:
    """PlayoutEngine should accept media from a ScheduleEvent."""
    engine = PlayoutEngine()
    event = make_event()

    engine.start()

    with patch.object(
        engine,
        "_validate_media",
        return_value=None,
    ):
        engine.play(event)

    assert engine.state is PlayoutState.PLAYING
    assert engine.current_event == event


def test_playout_engine_can_complete_scheduled_media() -> None:
    """A playing event should transition to a completed result."""
    engine = PlayoutEngine()
    event = make_event()

    engine.start()

    with patch.object(
        engine,
        "_validate_media",
        return_value=None,
    ):
        engine.play(event)

    result = engine.complete()

    assert result is not None
    assert result.event_id == event.event_id
    assert engine.current_event is None


@patch("chronoplay.output.Popen")
def test_output_can_be_started_for_scheduled_media(
    mock_popen: MagicMock,
) -> None:
    """The output layer should accept media from a scheduled event."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    event = make_event()
    output = make_output()

    output.start(str(event.payload.path))

    assert output.health() is True
    assert output.process is process


@patch("chronoplay.output.Popen")
def test_schedule_to_output_integration(
    mock_popen: MagicMock,
) -> None:
    """A scheduled media event should be usable by the output layer."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    scheduler = Scheduler()
    event = make_event()
    output = make_output()

    scheduler.add(event)

    scheduled_event = scheduler.get(event.event_id)

    assert scheduled_event is not None

    output.start(str(scheduled_event.payload.path))

    assert output.health() is True
    assert output.state.value == "running"

    output.stop()

    assert output.process is None
