from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from threading import Event, RLock
from typing import Any
from uuid import uuid4

UTC = timezone.utc


class SchedulerError(Exception):
    """Base exception for scheduler-related errors."""


class ScheduleValidationError(SchedulerError, ValueError):
    """Raised when a scheduled event contains invalid timing information."""


class EventNotFoundError(SchedulerError, KeyError):
    """Raised when an operation references an unknown event."""


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    """An immutable event scheduled for execution at an absolute time.

    Parameters
    ----------
    start:
        Absolute, timezone-aware execution time. The value is normalized to UTC.
    duration:
        Optional non-negative duration of the event.
    payload:
        Application-specific event data.
    event_id:
        Stable identifier. One is generated automatically when omitted.
    """

    start: datetime
    duration: timedelta | None = None
    payload: Any = None
    event_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        """Validate and normalize event timing."""
        if self.start.tzinfo is None or self.start.utcoffset() is None:
            raise ScheduleValidationError("ScheduleEvent.start must be timezone-aware.")

        if self.duration is not None and self.duration < timedelta(0):
            raise ScheduleValidationError("Event duration cannot be negative.")

        if not self.event_id.strip():
            raise ScheduleValidationError("event_id cannot be empty.")

        object.__setattr__(self, "start", self.start.astimezone(UTC))

    @property
    def end(self) -> datetime | None:
        """Return the expected end time when the event has a duration."""
        if self.duration is None:
            return None

        return self.start + self.duration


@dataclass(frozen=True, slots=True)
class _QueueItem:
    """Internal heap entry used to guarantee deterministic ordering."""

    start_timestamp: float
    sequence: int
    event: ScheduleEvent

    def __lt__(self, other: _QueueItem) -> bool:
        """Order events by time and then insertion sequence."""
        return (self.start_timestamp, self.sequence) < (
            other.start_timestamp,
            other.sequence,
        )


class Scheduler:
    """Thread-safe deterministic scheduler.

    Events are ordered first by UTC execution time and then by insertion
    sequence. Two events with identical timestamps therefore execute in the
    order in which they were scheduled.

    The scheduler does not perform media playback. Callbacks receive the
    :class:`ScheduleEvent` and are responsible for executing its payload.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize an empty scheduler."""
        self._clock = clock or self._utc_now
        self._queue: list[_QueueItem] = []
        self._events: dict[str, ScheduleEvent] = {}
        self._cancelled: set[str] = set()
        self._sequence = 0
        self._lock = RLock()
        self._stop_event = Event()

    @staticmethod
    def _utc_now() -> datetime:
        """Return the current timezone-aware UTC time."""
        return datetime.now(UTC)

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        """Validate and normalize a datetime to UTC."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ScheduleValidationError(
                "Scheduler times must be timezone-aware."
            )

        return value.astimezone(UTC)

    def schedule(self, event: ScheduleEvent) -> str:
        """Add an event and return its stable identifier."""
        with self._lock:
            if event.event_id in self._events:
                raise ScheduleValidationError(
                    f"Event ID already exists: {event.event_id}"
                )

            normalized = ScheduleEvent(
                start=self._normalize_datetime(event.start),
                duration=event.duration,
                payload=event.payload,
                event_id=event.event_id,
            )

            item = _QueueItem(
                start_timestamp=normalized.start.timestamp(),
                sequence=self._sequence,
                event=normalized,
            )

            self._sequence += 1
            self._events[normalized.event_id] = normalized
            heappush(self._queue, item)

            return normalized.event_id

    def cancel(self, event_id: str) -> ScheduleEvent:
        """Cancel a pending event and return it."""
        with self._lock:
            event = self._events.get(event_id)

            if event is None:
                raise EventNotFoundError(event_id)

            self._cancelled.add(event_id)
            del self._events[event_id]

            return event

    def get(self, event_id: str) -> ScheduleEvent:
        """Return a pending event by ID."""
        with self._lock:
            try:
                return self._events[event_id]
            except KeyError as exc:
                raise EventNotFoundError(event_id) from exc

    def __len__(self) -> int:
        """Return the number of pending, non-cancelled events."""
        with self._lock:
            return len(self._events)

    def pending(self) -> tuple[ScheduleEvent, ...]:
        """Return pending events in deterministic execution order."""
        with self._lock:
            events = [
                item.event
                for item in self._queue
                if item.event.event_id in self._events
            ]

            events.sort(key=lambda event: event.start.timestamp())
            return tuple(events)

    def pop_next(self) -> ScheduleEvent | None:
        """Remove and return the next pending event."""
        with self._lock:
            while self._queue:
                item = heappop(self._queue)
                event_id = item.event.event_id

                if event_id in self._cancelled:
                    self._cancelled.remove(event_id)
                    continue

                event = self._events.pop(event_id, None)

                if event is not None:
                    return event

            return None

    def next_event(self) -> ScheduleEvent | None:
        """Return the next pending event without removing it."""
        with self._lock:
            while self._queue:
                item = self._queue[0]
                event_id = item.event.event_id

                if event_id in self._cancelled:
                    heappop(self._queue)
                    self._cancelled.remove(event_id)
                    continue

                event = self._events.get(event_id)

                if event is not None:
                    return event

            return None

    def clear(self) -> tuple[ScheduleEvent, ...]:
        """Cancel and remove all pending events."""
        with self._lock:
            events = tuple(self._events.values())
            self._events.clear()
            self._cancelled.clear()
            self._queue.clear()
            return events

    def stop(self) -> None:
        """Request termination of a running scheduler loop."""
        self._stop_event.set()

    def reset_stop(self) -> None:
        """Reset the scheduler's stop request before another run."""
        self._stop_event.clear()

    def run(
        self,
        callback: Callable[[ScheduleEvent], Any],
        *,
        sleep_interval: float = 0.25,
    ) -> None:
        """Execute scheduled events when their start times are reached.

        Events that are already overdue execute immediately. The callback is
        invoked synchronously in deterministic schedule order.

        Parameters
        ----------
        callback:
            Function responsible for executing an event.
        sleep_interval:
            Maximum polling interval in seconds while waiting for an event.
        """
        if sleep_interval <= 0:
            raise ValueError("sleep_interval must be greater than zero.")

        self.reset_stop()

        while not self._stop_event.is_set():
            event = self.next_event()

            if event is None:
                self._stop_event.wait(sleep_interval)
                continue

            now = self._normalize_datetime(self._clock())
            remaining = (event.start - now).total_seconds()

            if remaining > 0:
                self._stop_event.wait(min(remaining, sleep_interval))
                continue

            event = self.pop_next()

            if event is not None:
                callback(event)

    def iter_pending(self) -> Iterator[ScheduleEvent]:
        """Iterate over pending events in deterministic order."""
        yield from self.pending()
