from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Thread
from time import sleep

import pytest

from chronoplay.scheduler import (
    EventNotFoundError,
    ScheduleEvent,
    Scheduler,
    ScheduleValidationError,
)

UTC = timezone.utc


def test_schedule_event_normalizes_start_to_utc() -> None:
    """ScheduleEvent should normalize timezone-aware timestamps to UTC."""
    start = datetime(
        2026,
        8,
        21,
        18,
        0,
        tzinfo=timezone(timedelta(hours=6)),
    )

    event = ScheduleEvent(start=start)

    assert event.start.tzinfo == UTC
    assert event.start == datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


def test_schedule_event_rejects_naive_datetime() -> None:
    """ScheduleEvent should reject timestamps without timezone information."""
    with pytest.raises(
        ScheduleValidationError,
        match="must be timezone-aware",
    ):
        ScheduleEvent(start=datetime(2026, 8, 21, 12, 0))


def test_schedule_event_rejects_negative_duration() -> None:
    """ScheduleEvent should reject negative durations."""
    with pytest.raises(
        ScheduleValidationError,
        match="duration cannot be negative",
    ):
        ScheduleEvent(
            start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
            duration=timedelta(seconds=-1),
        )


def test_schedule_event_rejects_empty_event_id() -> None:
    """ScheduleEvent should reject empty event identifiers."""
    with pytest.raises(
        ScheduleValidationError,
        match="event_id cannot be empty",
    ):
        ScheduleEvent(
            start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
            event_id="   ",
        )


def test_schedule_event_generates_event_id() -> None:
    """ScheduleEvent should generate a non-empty identifier."""
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    assert event.event_id


def test_schedule_event_end_is_calculated() -> None:
    """An event with a duration should expose its expected end time."""
    start = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    event = ScheduleEvent(
        start=start,
        duration=timedelta(minutes=30),
    )

    assert event.end == datetime(2026, 8, 21, 12, 30, tzinfo=UTC)


def test_schedule_event_without_duration_has_no_end() -> None:
    """An event without a duration should have no calculated end."""
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    assert event.end is None


def test_scheduler_starts_empty() -> None:
    """A new scheduler should contain no pending events."""
    scheduler = Scheduler()

    assert len(scheduler) == 0
    assert scheduler.next_event() is None
    assert scheduler.pending() == ()


def test_schedule_returns_event_id() -> None:
    """Scheduling an event should return its identifier."""
    scheduler = Scheduler()
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    event_id = scheduler.schedule(event)

    assert event_id == event.event_id
    assert len(scheduler) == 1


def test_schedule_preserves_event_payload() -> None:
    """Scheduled events should preserve application-specific payloads."""
    scheduler = Scheduler()
    payload = {
        "media": "program-001.mp4",
        "channel": "main",
    }
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
        payload=payload,
    )

    scheduler.schedule(event)

    assert scheduler.get(event.event_id).payload == payload


def test_scheduler_orders_events_by_start_time() -> None:
    """Events should execute in chronological order."""
    scheduler = Scheduler()

    late = ScheduleEvent(
        start=datetime(2026, 8, 21, 14, 0, tzinfo=UTC),
        event_id="late",
    )
    early = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
        event_id="early",
    )
    middle = ScheduleEvent(
        start=datetime(2026, 8, 21, 13, 0, tzinfo=UTC),
        event_id="middle",
    )

    scheduler.schedule(late)
    scheduler.schedule(early)
    scheduler.schedule(middle)

    assert [event.event_id for event in scheduler.pending()] == [
        "early",
        "middle",
        "late",
    ]


def test_scheduler_preserves_insertion_order_for_equal_timestamps() -> None:
    """Equal-time events should execute in scheduling order."""
    scheduler = Scheduler()
    start = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)

    first = ScheduleEvent(start=start, event_id="first")
    second = ScheduleEvent(start=start, event_id="second")
    third = ScheduleEvent(start=start, event_id="third")

    scheduler.schedule(first)
    scheduler.schedule(second)
    scheduler.schedule(third)

    assert scheduler.pop_next() == first
    assert scheduler.pop_next() == second
    assert scheduler.pop_next() == third


def test_next_event_does_not_remove_event() -> None:
    """next_event should inspect without consuming the event."""
    scheduler = Scheduler()
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    scheduler.schedule(event)

    assert scheduler.next_event() == event
    assert scheduler.next_event() == event
    assert len(scheduler) == 1


def test_pop_next_removes_event() -> None:
    """pop_next should consume the next pending event."""
    scheduler = Scheduler()
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    scheduler.schedule(event)

    assert scheduler.pop_next() == event
    assert len(scheduler) == 0
    assert scheduler.next_event() is None


def test_pop_next_returns_none_when_empty() -> None:
    """pop_next should return None when no events are pending."""
    scheduler = Scheduler()

    assert scheduler.pop_next() is None


def test_get_returns_pending_event() -> None:
    """get should return a scheduled event by identifier."""
    scheduler = Scheduler()
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    scheduler.schedule(event)

    assert scheduler.get(event.event_id) == event


def test_get_raises_for_unknown_event() -> None:
    """get should reject unknown event identifiers."""
    scheduler = Scheduler()

    with pytest.raises(EventNotFoundError):
        scheduler.get("missing")


def test_cancel_removes_event() -> None:
    """cancel should remove and return a pending event."""
    scheduler = Scheduler()
    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )

    scheduler.schedule(event)

    cancelled = scheduler.cancel(event.event_id)

    assert cancelled == event
    assert len(scheduler) == 0
    assert scheduler.next_event() is None


def test_cancel_raises_for_unknown_event() -> None:
    """cancel should reject unknown event identifiers."""
    scheduler = Scheduler()

    with pytest.raises(EventNotFoundError):
        scheduler.cancel("missing")


def test_cancelled_event_is_not_returned_by_pop_next() -> None:
    """Cancelled events should never be returned by the queue."""
    scheduler = Scheduler()
    cancelled = ScheduleEvent(
        start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
        event_id="cancelled",
    )
    active = ScheduleEvent(
        start=datetime(2026, 8, 21, 13, 0, tzinfo=UTC),
        event_id="active",
    )

    scheduler.schedule(cancelled)
    scheduler.schedule(active)
    scheduler.cancel(cancelled.event_id)

    assert scheduler.pop_next() == active
    assert scheduler.pop_next() is None


def test_clear_returns_all_pending_events() -> None:
    """clear should remove and return every pending event."""
    scheduler = Scheduler()

    events = (
        ScheduleEvent(
            start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
            event_id="one",
        ),
        ScheduleEvent(
            start=datetime(2026, 8, 21, 13, 0, tzinfo=UTC),
            event_id="two",
        ),
    )

    for event in events:
        scheduler.schedule(event)

    cleared = scheduler.clear()

    assert set(cleared) == set(events)
    assert len(scheduler) == 0
    assert scheduler.next_event() is None


def test_iter_pending_matches_pending() -> None:
    """iter_pending should expose the same deterministic ordering."""
    scheduler = Scheduler()

    events = (
        ScheduleEvent(
            start=datetime(2026, 8, 21, 14, 0, tzinfo=UTC),
            event_id="late",
        ),
        ScheduleEvent(
            start=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
            event_id="early",
        ),
    )

    for event in events:
        scheduler.schedule(event)

    assert tuple(scheduler.iter_pending()) == scheduler.pending()


def test_scheduler_run_executes_overdue_event() -> None:
    """run should immediately execute an event that is already due."""
    current_time = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    scheduler = Scheduler(clock=lambda: current_time)

    event = ScheduleEvent(
        start=current_time - timedelta(seconds=1),
        event_id="overdue",
    )
    scheduler.schedule(event)

    executed: list[str] = []

    def callback(item: ScheduleEvent) -> None:
        executed.append(item.event_id)
        scheduler.stop()

    scheduler.run(callback)

    assert executed == ["overdue"]
    assert len(scheduler) == 0


def test_scheduler_run_executes_events_in_order() -> None:
    """run should execute due events in deterministic order."""
    current_time = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    scheduler = Scheduler(clock=lambda: current_time)

    scheduler.schedule(
        ScheduleEvent(
            start=current_time,
            event_id="first",
        )
    )
    scheduler.schedule(
        ScheduleEvent(
            start=current_time,
            event_id="second",
        )
    )
    scheduler.schedule(
        ScheduleEvent(
            start=current_time,
            event_id="third",
        )
    )

    executed: list[str] = []

    def callback(event: ScheduleEvent) -> None:
        executed.append(event.event_id)

        if len(executed) == 3:
            scheduler.stop()

    scheduler.run(callback)

    assert executed == ["first", "second", "third"]


def test_scheduler_run_rejects_non_positive_sleep_interval() -> None:
    """run should reject invalid polling intervals."""
    scheduler = Scheduler()

    with pytest.raises(
        ValueError,
        match="sleep_interval must be greater than zero",
    ):
        scheduler.run(lambda _: None, sleep_interval=0)


def test_scheduler_stop_terminates_waiting_run() -> None:
    """stop should interrupt a scheduler waiting for the next event."""
    scheduler = Scheduler()
    scheduler.schedule(
        ScheduleEvent(
            start=datetime.now(UTC) + timedelta(hours=1),
            event_id="future",
        )
    )

    worker = Thread(
        target=scheduler.run,
        args=(lambda _: None,),
        kwargs={"sleep_interval": 0.01},
    )

    worker.start()
    sleep(0.02)
    scheduler.stop()
    worker.join(timeout=1)

    assert not worker.is_alive()


def test_scheduler_can_be_restarted_after_stop() -> None:
    """A stopped scheduler should be reusable after reset."""
    current_time = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    scheduler = Scheduler(clock=lambda: current_time)

    scheduler.stop()
    scheduler.reset_stop()

    scheduler.schedule(
        ScheduleEvent(
            start=current_time,
            event_id="restart",
        )
    )

    executed: list[str] = []

    def callback(event: ScheduleEvent) -> None:
        executed.append(event.event_id)
        scheduler.stop()

    scheduler.run(callback)

    assert executed == ["restart"]


def test_scheduler_accepts_non_utc_timezone() -> None:
    """Scheduler should accept any valid timezone-aware datetime."""
    dhaka = timezone(timedelta(hours=6))
    scheduler = Scheduler()

    event = ScheduleEvent(
        start=datetime(2026, 8, 21, 18, 0, tzinfo=dhaka),
        event_id="dhaka-event",
    )

    scheduler.schedule(event)

    assert scheduler.get("dhaka-event").start == datetime(
        2026,
        8,
        21,
        12,
        0,
        tzinfo=UTC,
    )


def test_scheduler_rejects_duplicate_event_id() -> None:
    """Two pending events cannot share the same identifier."""
    scheduler = Scheduler()
    start = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)

    scheduler.schedule(
        ScheduleEvent(
            start=start,
            event_id="duplicate",
        )
    )

    with pytest.raises(
        ScheduleValidationError,
        match="Event ID already exists",
    ):
        scheduler.schedule(
            ScheduleEvent(
                start=start + timedelta(minutes=1),
                event_id="duplicate",
            )
       
       )
