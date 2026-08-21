from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from time import monotonic

UTC = timezone.utc


class ClockError(RuntimeError):
    """Raised when the ChronoPlay clock encounters an invalid state."""


class Clock:
    """Provide authoritative wall-clock and monotonic time.

    The wall clock is always returned as a timezone-aware UTC datetime.
    The monotonic clock is suitable for measuring elapsed durations and is
    independent of system clock adjustments.

    A callable time source can be injected for deterministic testing.
    """

    def __init__(
        self,
        *,
        time_source: Callable[[], datetime] | None = None,
        monotonic_source: Callable[[], float] | None = None,
    ) -> None:
        """Initialize the clock with optional injectable time sources."""
        self._time_source = time_source or self._utc_now
        self._monotonic_source = monotonic_source or monotonic

    @staticmethod
    def _utc_now() -> datetime:
        """Return the current timezone-aware UTC time."""
        return datetime.now(UTC)

    def now(self) -> datetime:
        """Return the current authoritative time in UTC."""
        value = self._time_source()

        if value.tzinfo is None or value.utcoffset() is None:
            raise ClockError("Clock time source must return a timezone-aware datetime.")

        return value.astimezone(UTC)

    def monotonic(self) -> float:
        """Return a monotonic timestamp suitable for elapsed-time measurement."""
        return self._monotonic_source()

    def elapsed(self, start: float) -> float:
        """Return elapsed monotonic seconds since ``start``."""
        return self.monotonic() - start

    def timestamp(self) -> float:
        """Return the current UTC time as a POSIX timestamp."""
        return self.now().timestamp()

    def is_before(self, target: datetime) -> bool:
        """Return whether the current UTC time is before ``target``."""
        return self.now() < self._normalize_datetime(target)

    def is_due(self, target: datetime) -> bool:
        """Return whether the current UTC time has reached ``target``."""
        return self.now() >= self._normalize_datetime(target)

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        """Validate and normalize a datetime to UTC."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ClockError("Clock times must be timezone-aware.")

        return value.astimezone(UTC)
