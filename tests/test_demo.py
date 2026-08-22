from pathlib import Path

import pytest

from chronoplay.demo import create_demo_schedule, main, run_demo
from chronoplay.models import MediaAsset


def test_create_demo_schedule(tmp_path: Path) -> None:
    media_path = tmp_path / "demo.mp4"

    schedule = create_demo_schedule(media_path)

    assert schedule is not None
    assert len(schedule.events) == 1

    event = schedule.events[0]

    assert event.event_id == "demo-program"
    assert isinstance(event.payload, MediaAsset)
    assert event.payload.path == media_path
    assert event.payload.duration == 300
    assert event.start_time.tzinfo is not None


def test_run_demo_starts_plays_and_stops(monkeypatch, tmp_path: Path) -> None:
    media_path = tmp_path / "demo.mp4"
    media_path.touch()

    calls = []

    class FakeEngine:
        def start(self):
            calls.append("start")

        def play(self, asset):
            calls.append(("play", asset))

        def stop(self):
            calls.append("stop")

    monkeypatch.setattr(
        "chronoplay.demo.PlayoutEngine",
        lambda: FakeEngine(),
    )

    run_demo(media_path)

    assert calls[0] == "start"
    assert calls[1][0] == "play"
    assert calls[1][1].path == media_path
    assert calls[2] == "stop"


def test_run_demo_does_not_start_with_empty_schedule(monkeypatch, tmp_path: Path) -> None:
    media_path = tmp_path / "demo.mp4"

    class FakeEngine:
        def __init__(self):
            pytest.fail("PlayoutEngine should not be created for an empty schedule")

    monkeypatch.setattr(
        "chronoplay.demo.PlayoutEngine",
        FakeEngine,
    )
    monkeypatch.setattr(
        "chronoplay.demo.create_demo_schedule",
        lambda _: [],
    )

    run_demo(media_path)


def test_run_demo_stops_when_play_fails(monkeypatch, tmp_path: Path) -> None:
    media_path = tmp_path / "demo.mp4"
    media_path.touch()

    calls = []

    class FakeEngine:
        def start(self):
            calls.append("start")

        def play(self, asset):
            calls.append("play")
            raise RuntimeError("playback failed")

        def stop(self):
            calls.append("stop")

    monkeypatch.setattr(
        "chronoplay.demo.PlayoutEngine",
        lambda: FakeEngine(),
    )

    with pytest.raises(RuntimeError, match="playback failed"):
        run_demo(media_path)

    assert calls == ["start", "play", "stop"]


def test_main_requires_demo_media(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match="Demo media file was not found",
    ):
        main()


def test_main_runs_demo(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    media_path = tmp_path / "demo.mp4"
    media_path.touch()

    called = []

    monkeypatch.setattr(
        "chronoplay.demo.run_demo",
        lambda path: called.append(path),
    )

    main()

    assert called == [Path("demo.mp4")]
