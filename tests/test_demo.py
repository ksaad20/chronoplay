from __future__ import annotations

from pathlib import Path

import pytest

from chronoplay.demo import create_demo_schedule, main, run_demo


def test_create_demo_schedule(tmp_path: Path) -> None:
    """Create a scheduler containing the expected demo event."""
    media_path = tmp_path / "demo.mp4"

    scheduler = create_demo_schedule(media_path)
    event = scheduler.pop_next()

    assert event is not None
    assert event.event_id == "demo-program"
    assert event.payload.path == media_path
    assert event.payload.duration == 300
    assert event.duration is not None
    assert event.duration.total_seconds() == 300


def test_create_demo_schedule_accepts_string_path(tmp_path: Path) -> None:
    """Accept a media path supplied as a string."""
    media_path = tmp_path / "demo.mp4"

    scheduler = create_demo_schedule(str(media_path))
    event = scheduler.pop_next()

    assert event is not None
    assert event.payload.path == media_path


def test_run_demo_starts_plays_and_stops(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Start the playout engine, play the event, and stop the engine."""
    media_path = tmp_path / "demo.mp4"
    calls: list[str] = []

    class FakeEngine:
        def start(self) -> None:
            calls.append("start")

        def play(self, event: object) -> None:
            calls.append("play")
            assert event.event_id == "demo-program"

        def stop(self) -> None:
            calls.append("stop")

    monkeypatch.setattr("chronoplay.demo.PlayoutEngine", FakeEngine)

    run_demo(media_path)

    assert calls == ["start", "play", "stop"]


def test_run_demo_stops_after_play_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Stop the playout engine even when playback raises an exception."""
    media_path = tmp_path / "demo.mp4"
    calls: list[str] = []

    class FakeEngine:
        def start(self) -> None:
            calls.append("start")

        def play(self, event: object) -> None:
            calls.append("play")
            raise RuntimeError("playback failed")

        def stop(self) -> None:
            calls.append("stop")

    monkeypatch.setattr("chronoplay.demo.PlayoutEngine", FakeEngine)

    with pytest.raises(RuntimeError, match="playback failed"):
        run_demo(media_path)

    assert calls == ["start", "play", "stop"]


def test_run_demo_handles_empty_schedule(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Return without starting playout when the schedule is empty."""
    media_path = tmp_path / "demo.mp4"
    calls: list[str] = []

    class EmptyScheduler:
        def pop_next(self) -> None:
            return None

    class FakeEngine:
        def __init__(self) -> None:
            calls.append("engine_created")

        def start(self) -> None:
            calls.append("start")

        def stop(self) -> None:
            calls.append("stop")

    monkeypatch.setattr(
        "chronoplay.demo.create_demo_schedule",
        lambda _: EmptyScheduler(),
    )
    monkeypatch.setattr("chronoplay.demo.PlayoutEngine", FakeEngine)

    run_demo(media_path)

    assert calls == ["engine_created"]


def test_main_requires_demo_media(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Raise FileNotFoundError when demo.mp4 is missing."""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match=r"Demo media file was not found: demo\.mp4",
    ):
        main()


def test_main_runs_demo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Run the demo using the default demo.mp4 path."""
    monkeypatch.chdir(tmp_path)

    media_path = tmp_path / "demo.mp4"
    media_path.touch()

    called: list[Path] = []

    def fake_run_demo(path: str | Path) -> None:
        called.append(Path(path))

    monkeypatch.setattr("chronoplay.demo.run_demo", fake_run_demo)

    main()

    assert called == [Path("demo.mp4")]
