"""Deterministic, timezone-aware scheduling primitives for ChronoPlay."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from threading import Event, RLock
from typing import Any
from uuid import uuid4


UTC = timezone.utc


class ScheduleValidationError(ValueError):
    """Raised when a scheduled event contains invalid timing information."""


class EventNotFoundError(KeyError):
    """Raised when an operation references an unknown event."""


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    """Immutable event scheduled for execution at an absolute time."""

    start: datetime
    duration: timedelta | None = None
    payload: Any = None
    event_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        """Validate and normalize event timing."""
        if self.start.tzinfo is None or self.start.utcoffset() is None:
            raise ScheduleValidationError(
                "ScheduleEvent.start must be timezone-aware."
            )

        if self.duration is not None and self.duration < timedelta(0):
            raise ScheduleValidationError("Event duration cannot be negative.")

        if not self.event_id.strip():
            raise ScheduleValidationError("event_id cannot be empty.")

        object.__setattr__(self, "start", self.start.astimezone(UTC))

    @property
    def end(self) -> datetime | None:
        """Return the expected end time when a duration is defined."""
        if self.duration is None:
            return None

        return self.start + self.duration


class Scheduler:
    """Thread-safe deterministic scheduler.

    Events are ordered by UTC execution time and insertion sequence.
    Events with identical timestamps therefore execute in scheduling order.

    The scheduler does not perform media playback. The callback supplied to
    :meth:`run` is responsible for executing each event.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Initialize an empty scheduler."""
        self._clock = clock or self._utc_now
        self._queue: list[tuple[float, int, ScheduleEvent]] = []
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

            heappush(
                self._queue,
                (
                    normalized.start.timestamp(),
                    self._sequence,
                    normalized,
                ),
            )
            self._sequence += 1
            self._events[normalized.event_id] = normalized

            return normalized.event_id

    def cancel(self, event_id: str) -> ScheduleEvent:
        """Cancel a pending event and return it."""
        with self._lock:
            event = self._events.pop(event_id, None)

            if event is None:
                raise EventNotFoundError(event_id)

            self._cancelled.add(event_id)
            return event

    def get(self, event_id: str) -> ScheduleEvent:
        """Return a pending event by ID."""
        with self._lock:
            event = self._events.get(event_id)

            if event is None:
                raise EventNotFoundError(event_id)

            return event

    def __len__(self) -> int:
        """Return the number of pending events."""
        with self._lock:
            return len(self._events)

    def pending(self) -> tuple[ScheduleEvent, ...]:
        """Return pending events in deterministic execution order."""
        with self._lock:
            return tuple(
                sorted(
                    self._events.values(),
                    key=lambda event: event.start.timestamp(),
                )
            )

    def next_event(self) -> ScheduleEvent | None:
        """Return the next pending event without removing it."""
        with self._lock:
            self._discard_cancelled()

            if not self._queue:
                return None

            return self._queue[0][2]

    def pop_next(self) -> ScheduleEvent | None:
        """Remove and return the next pending event."""
        with self._lock:
            self._discard_cancelled()

            if not self._queue:
                return None

            _, _, event = heappop(self._queue)
            self._events.pop(event.event_id, None)

            return event

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
        """Reset the scheduler stop request."""
        self._stop_event.clear()

    def run(
        self,
        callback: Callable[[ScheduleEvent], Any],
        *,
        sleep_interval: float = 0.25,
    ) -> None:
        """Execute events when their scheduled start times are reached."""
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
        """Iterate over pending events in deterministic execution order."""
        yield from self.pending()

    def _discard_cancelled(self) -> None:
        """Remove cancelled events from the head of the queue."""
        while self._queue and self._queue[0][2].event_id in self._cancelled:
            _, _, event = heappop(self._queue)
            self._cancelled.discard(event.event_id)
