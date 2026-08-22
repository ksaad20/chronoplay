from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chronoplay.demo import create_demo_schedule, main, run_demo
from chronoplay.media import MediaAsset


def test_create_demo_schedule_creates_event(tmp_path: Path) -> None:
    """The demo schedule should contain one media event."""
    media_path = tmp_path / "demo.mp4"

    scheduler = create_demo_schedule(media_path)
    event = scheduler.pop_next()

    assert event is not None
    assert event.event_id == "demo-program"
    assert event.payload == MediaAsset(path=media_path, duration=300)
    assert event.duration == timedelta(seconds=300)


def test_create_demo_schedule_uses_timezone_aware_start(
    tmp_path: Path,
) -> None:
    """The demo event should use a timezone-aware start time."""
    scheduler = create_demo_schedule(tmp_path / "demo.mp4")
    event = scheduler.pop_next()

    assert event is not None
    assert event.start.tzinfo is not None
    assert event.start.utcoffset() is not None


@patch("chronoplay.demo.PlayoutEngine")
def test_run_demo_plays_and_stops_engine(
    mock_engine_class: MagicMock,
    tmp_path: Path,
) -> None:
    """The demo should start, play, and stop the playout engine."""
    engine = mock_engine_class.return_value
    media_path = tmp_path / "demo.mp4"

    run_demo(media_path)

    engine.start.assert_called_once()
    engine.play.assert_called_once()
    engine.stop.assert_called_once()


@patch("chronoplay.demo.PlayoutEngine")
def test_run_demo_does_not_play_when_schedule_is_empty(
    mock_engine_class: MagicMock,
    tmp_path: Path,
) -> None:
    """An empty schedule should not start the playout engine."""
    with patch(
        "chronoplay.demo.create_demo_schedule",
    ) as mock_schedule:
        mock_schedule.return_value.pop_next.return_value = None

        run_demo(tmp_path / "demo.mp4")

    engine = mock_engine_class.return_value
    engine.start.assert_not_called()
    engine.play.assert_not_called()
    engine.stop.assert_not_called()


def test_main_requires_demo_media(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The demo entry point should require demo.mp4."""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match="Demo media file was not found"):
        main()


@patch("chronoplay.demo.run_demo")
def test_main_runs_demo_for_demo_mp4(
    mock_run_demo: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The demo entry point should run when demo.mp4 exists."""
    monkeypatch.chdir(tmp_path)
    media_path = tmp_path / "demo.mp4"
    media_path.touch()

    main()

    mock_run_demo.assert_called_once_with(Path("demo.mp4"))


@patch("chronoplay.demo.PlayoutEngine")
def test_run_demo_stops_engine_when_play_fails(
    mock_engine_class: MagicMock,
    tmp_path: Path,
) -> None:
    """The demo should stop the engine when playout fails."""
    engine = mock_engine_class.return_value
    engine.play.side_effect = RuntimeError("playout failed")

    with pytest.raises(RuntimeError, match="playout failed"):
        run_demo(tmp_path / "demo.mp4")

    engine.start.assert_called_once()
    engine.play.assert_called_once()
    engine.stop.assert_called_once()
```
