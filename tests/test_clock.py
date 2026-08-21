from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from chronoplay.clock import UTC, Clock, ClockError


def test_clock_returns_current_time_in_utc() -> None:
    """Clock.now should return a timezone-aware UTC datetime."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    result = clock.now()

    assert result == current
    assert result.tzinfo == UTC


def test_clock_normalizes_other_timezones_to_utc() -> None:
    """Clock.now should normalize timezone-aware values to UTC."""
    dhaka = timezone(timedelta(hours=6))
    current = datetime(2026, 8, 21, 21, 0, tzinfo=dhaka)
    clock = Clock(time_source=lambda: current)

    result = clock.now()

    assert result == datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    assert result.tzinfo == UTC


def test_clock_rejects_naive_time_source() -> None:
    """Clock.now should reject a naive datetime from its time source."""
    clock = Clock(
        time_source=lambda: datetime(2026, 8, 21, 15, 0),
    )

    with pytest.raises(
        ClockError,
        match="must return a timezone-aware datetime",
    ):
        clock.now()


def test_clock_monotonic_uses_injected_source() -> None:
    """Clock.monotonic should use the injected monotonic source."""
    clock = Clock(monotonic_source=lambda: 42.5)

    assert clock.monotonic() == 42.5


def test_clock_elapsed_uses_monotonic_time() -> None:
    """Clock.elapsed should calculate elapsed monotonic seconds."""
    values = iter((100.0, 104.75))
    clock = Clock(monotonic_source=lambda: next(values))

    start = clock.monotonic()

    assert clock.elapsed(start) == 4.75


def test_clock_timestamp_returns_utc_posix_timestamp() -> None:
    """Clock.timestamp should return the UTC POSIX timestamp."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert clock.timestamp() == current.timestamp()


def test_clock_is_before_returns_true_for_future_time() -> None:
    """Clock.is_before should identify future targets."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    target = datetime(2026, 8, 21, 15, 1, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert clock.is_before(target)


def test_clock_is_before_returns_false_for_current_time() -> None:
    """Clock.is_before should return false when the target has been reached."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert not clock.is_before(current)


def test_clock_is_before_returns_false_for_past_time() -> None:
    """Clock.is_before should return false for an elapsed target."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    target = datetime(2026, 8, 21, 14, 59, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert not clock.is_before(target)


def test_clock_is_due_returns_false_for_future_time() -> None:
    """Clock.is_due should return false before a target is reached."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    target = datetime(2026, 8, 21, 15, 1, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert not clock.is_due(target)


def test_clock_is_due_returns_true_at_target_time() -> None:
    """Clock.is_due should return true at the exact target time."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert clock.is_due(current)


def test_clock_is_due_returns_true_after_target_time() -> None:
    """Clock.is_due should return true after a target has passed."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    target = datetime(2026, 8, 21, 14, 59, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    assert clock.is_due(target)


def test_clock_rejects_naive_target_for_is_before() -> None:
    """Clock.is_before should reject a naive target."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    with pytest.raises(
        ClockError,
        match="Clock times must be timezone-aware",
    ):
        clock.is_before(datetime(2026, 8, 21, 15, 1))


def test_clock_rejects_naive_target_for_is_due() -> None:
    """Clock.is_due should reject a naive target."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    clock = Clock(time_source=lambda: current)

    with pytest.raises(
        ClockError,
        match="Clock times must be timezone-aware",
    ):
        clock.is_due(datetime(2026, 8, 21, 15, 1))


def test_clock_normalizes_timezone_aware_target() -> None:
    """Target comparisons should work across timezones."""
    current = datetime(2026, 8, 21, 15, 0, tzinfo=UTC)
    dhaka = timezone(timedelta(hours=6))
    target = datetime(2026, 8, 21, 21, 0, tzinfo=dhaka)
    clock = Clock(time_source=lambda: current)

    assert clock.is_due(target)


def test_clock_uses_default_time_source() -> None:
    """The default clock should provide a timezone-aware UTC datetime."""
    clock = Clock()

    result = clock.now()

    assert result.tzinfo == UTC
    assert result.utcoffset() == timedelta(0)


def test_clock_uses_default_monotonic_source() -> None:
    """The default monotonic source should return a numeric value."""
    clock = Clock()

    result = clock.monotonic()

    assert isinstance(result, float)


def test_clock_elapsed_can_measure_zero_duration() -> None:
    """Elapsed time should be zero when the source does not advance."""
    clock = Clock(monotonic_source=lambda: 100.0)

    start = clock.monotonic()

    assert clock.elapsed(start) == 0.0
