from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from chronoplay.media import MediaAsset
from chronoplay.playout import (
    PlayoutEngine,
    PlayoutError,
    PlayoutResult,
    PlayoutState,
)
from chronoplay.scheduler import ScheduleEvent


def make_event(
    tmp_path: Path,
    *,
    filename: str = "program.mp4",
    media_id: str = "program-001",
) -> ScheduleEvent:
    """Create a scheduled event backed by a test media asset."""
    media_path = tmp_path / filename
    media_path.write_bytes(b"test-media")

    asset = MediaAsset(
        path=media_path,
        media_id=media_id,
        title="Test Program",
    )

    return ScheduleEvent(
        start=datetime.now(timezone.utc),
        payload=asset,
    )


def test_engine_starts_stopped() -> None:
    """A new playout engine should be stopped."""
    engine = PlayoutEngine()

    assert engine.state is PlayoutState.STOPPED
    assert engine.current_event is None


def test_start_moves_engine_to_ready() -> None:
    """Starting the engine should make it ready for playback."""
    engine = PlayoutEngine()

    engine.start()

    assert engine.state is PlayoutState.READY


def test_start_is_idempotent_when_ready() -> None:
    """Starting an already-ready engine should remain safe."""
    engine = PlayoutEngine()

    engine.start()
    engine.start()

    assert engine.state is PlayoutState.READY


def test_stop_returns_engine_to_stopped() -> None:
    """Stopping the engine should clear its current event."""
    engine = PlayoutEngine()

    engine.start()
    engine.stop()

    assert engine.state is PlayoutState.STOPPED
    assert engine.current_event is None


def test_play_requires_started_engine(tmp_path: Path) -> None:
    """Playback should fail while the engine is stopped."""
    engine = PlayoutEngine()
    event = make_event(tmp_path)

    with pytest.raises(
        PlayoutError,
        match="must be started before playing",
    ):
        engine.play(event)


def test_play_accepts_media_event(tmp_path: Path) -> None:
    """A valid media event should enter the playing state."""
    engine = PlayoutEngine()
    event = make_event(tmp_path)

    engine.start()
    result = engine.play(event)

    assert result.event_id == event.event_id
    assert result.media_id == "program-001"
    assert result.media_path == str(tmp_path / "program.mp4")
    assert result.state is PlayoutState.PLAYING
    assert engine.state is PlayoutState.PLAYING
    assert engine.current_event == event


def test_complete_returns_result(tmp_path: Path) -> None:
    """Completing playback should return the engine to ready."""
    engine = PlayoutEngine()
    event = make_event(tmp_path)

    engine.start()
    engine.play(event)

    result = engine.complete()

    assert isinstance(result, PlayoutResult)
    assert result.event_id == event.event_id
    assert result.media_id == "program-001"
    assert result.state is PlayoutState.READY
    assert engine.state is PlayoutState.READY
    assert engine.current_event is None


def test_complete_without_current_event_returns_none() -> None:
    """Completing when idle should return None."""
    engine = PlayoutEngine()

    assert engine.complete() is None


def test_stop_clears_active_playback(tmp_path: Path) -> None:
    """Stopping active playback should clear the current event."""
    engine = PlayoutEngine()
    event = make_event(tmp_path)

    engine.start()
    engine.play(event)
    engine.stop()

    assert engine.state is PlayoutState.STOPPED
    assert engine.current_event is None


def test_reset_returns_engine_to_stopped(tmp_path: Path) -> None:
    """Reset should clear the current event and stop the engine."""
    engine = PlayoutEngine()
    event = make_event(tmp_path)

    engine.start()
    engine.play(event)
    engine.reset()

    assert engine.state is PlayoutState.STOPPED
    assert engine.current_event is None


def test_non_media_payload_is_rejected() -> None:
    """A schedule event without a MediaAsset should be rejected."""
    engine = PlayoutEngine()
    event = ScheduleEvent(
        start=datetime.now(timezone.utc),
        payload="not-media",
    )

    engine.start()

    with pytest.raises(
        PlayoutError,
        match="payload must contain a MediaAsset",
    ):
        engine.play(event)

    assert engine.state is PlayoutState.READY


def test_media_validation_failure_sets_error_state(
    tmp_path: Path,
) -> None:
    """A failed media validation should place the engine in error."""
    media_path = tmp_path / "missing.mp4"
    asset = MediaAsset(path=media_path)

    event = ScheduleEvent(
        start=datetime.now(timezone.utc),
        payload=asset,
    )

    engine = PlayoutEngine()
    engine.start()

    with pytest.raises(
        PlayoutError,
        match="Media validation failed",
    ):
        engine.play(event)

    assert engine.state is PlayoutState.ERROR
    assert engine.current_event is None


def test_error_state_rejects_new_playback(
    tmp_path: Path,
) -> None:
    """An errored engine should reject further playback."""
    missing_asset = MediaAsset(path=tmp_path / "missing.mp4")
    invalid_event = ScheduleEvent(
        start=datetime.now(timezone.utc),
        payload=missing_asset,
    )

    engine = PlayoutEngine()
    engine.start()

    with pytest.raises(PlayoutError):
        engine.play(invalid_event)

    valid_event = make_event(
        tmp_path,
        filename="valid.mp4",
        media_id="valid-001",
    )

    with pytest.raises(
        PlayoutError,
        match="error state",
    ):
        engine.play(valid_event)


def test_reset_recovers_error_state(
    tmp_path: Path,
) -> None:
    """Reset should recover an engine from an error state."""
    asset = MediaAsset(path=tmp_path / "missing.mp4")
    event = ScheduleEvent(
        start=datetime.now(timezone.utc),
        payload=asset,
    )

    engine = PlayoutEngine()
    engine.start()

    with pytest.raises(PlayoutError):
        engine.play(event)

    engine.reset()

    assert engine.state is PlayoutState.STOPPED
    assert engine.current_event is None


def test_custom_validator_is_used(tmp_path: Path) -> None:
    """A caller-provided validator should be invoked."""
    validated: list[MediaAsset] = []

    def validator(asset: MediaAsset) -> None:
        validated.append(asset)

    engine = PlayoutEngine(validator=validator)
    event = make_event(tmp_path)

    engine.start()
    engine.play(event)

    assert validated == [event.payload]


def test_custom_validator_failure_preserves_ready_state(
    tmp_path: Path,
) -> None:
    """A non-MediaError validator failure should preserve the ready state."""

    def validator(_: MediaAsset) -> None:
        raise ValueError("custom validation failed")

    engine = PlayoutEngine(validator=validator)
    event = make_event(tmp_path)

    engine.start()

    with pytest.raises(
        ValueError,
        match="custom validation failed",
    ):
        engine.play(event)

    assert engine.state is PlayoutState.READY
    assert engine.current_event is None
