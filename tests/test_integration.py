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


def make_event(
    event_id: str = "event-1",
    hour: int = 12,
) -> ScheduleEvent:
    """Create a scheduled media event."""
    return ScheduleEvent(
        event_id=event_id,
        start=datetime(2026, 8, 22, hour, 0, tzinfo=UTC),
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


def test_schedule_event_can_be_scheduled() -> None:
    """A valid media event should be accepted by the scheduler."""
    scheduler = Scheduler()
    event = make_event()

    event_id = scheduler.schedule(
        start=event.start,
        payload=event.payload,
        duration=event.duration,
        event_id=event.event_id,
    )

    assert event_id == event.event_id
    assert scheduler.get(event.event_id).payload == event.payload


def test_scheduler_preserves_media_event_order() -> None:
    """Scheduled media events should remain in chronological order."""
    scheduler = Scheduler()

    later = make_event("event-2", 13)
    earlier = make_event("event-1", 12)

    scheduler.schedule(
        start=later.start,
        payload=later.payload,
        duration=later.duration,
        event_id=later.event_id,
    )
    scheduler.schedule(
        start=earlier.start,
        payload=earlier.payload,
        duration=earlier.duration,
        event_id=earlier.event_id,
    )

    events = list(scheduler.iter_pending())

    assert [event.event_id for event in events] == [
        "event-1",
        "event-2",
    ]


def test_scheduled_media_can_be_retrieved_for_playout() -> None:
    """A scheduled media event should be retrievable for playout."""
    scheduler = Scheduler()
    event = make_event()

    scheduler.schedule(
        start=event.start,
        payload=event.payload,
        duration=event.duration,
        event_id=event.event_id,
    )

    scheduled_event = scheduler.get(event.event_id)

    assert scheduled_event.event_id == event.event_id
    assert scheduled_event.payload == event.payload


def test_playout_engine_can_play_scheduled_media() -> None:
    """PlayoutEngine should accept a valid scheduled media event."""
    engine = PlayoutEngine()
    event = make_event()

    engine.start()
    engine.play(event)

    assert engine.state is PlayoutState.PLAYING
    assert engine.current_event == event


def test_playout_engine_can_complete_scheduled_media() -> None:
    """A playing scheduled event should be completable."""
    engine = PlayoutEngine()
    event = make_event()

    engine.start()
    engine.play(event)

    result = engine.complete()

    assert result is not None
    assert result.event_id == event.event_id
    assert engine.current_event is None


@patch("chronoplay.output.Popen")
def test_scheduled_media_can_be_sent_to_output(
    mock_popen: MagicMock,
) -> None:
    """Scheduled media should be usable by the output backend."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    event = make_event()
    output = make_output()

    output.start(str(event.payload.path))

    assert output.state.value == "running"
    assert output.health() is True
    assert output.process is process

    output.stop()

    assert output.process is None


@patch("chronoplay.output.Popen")
def test_scheduler_playout_and_output_work_together(
    mock_popen: MagicMock,
) -> None:
    """A scheduled media event should flow through playout to output."""
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    scheduler = Scheduler()
    engine = PlayoutEngine()
    output = make_output()
    event = make_event()

    scheduler.schedule(
        start=event.start,
        payload=event.payload,
        duration=event.duration,
        event_id=event.event_id,
    )

    scheduled_event = scheduler.get(event.event_id)

    engine.start()
    engine.play(scheduled_event)
    output.start(str(scheduled_event.payload.path))

    assert engine.state is PlayoutState.PLAYING
    assert engine.current_event == scheduled_event
    assert output.health() is True

    output.stop()
    engine.complete()

    assert output.process is None
    assert engine.current_event is None
