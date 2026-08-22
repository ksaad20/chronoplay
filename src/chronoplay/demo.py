from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from chronoplay.media import MediaAsset
from chronoplay.playout import PlayoutEngine
from chronoplay.scheduler import ScheduleEvent, Scheduler

LOGGER = logging.getLogger(__name__)
UTC = timezone.utc


def create_demo_schedule(media_path: str | Path) -> Scheduler:
    """Create a small demonstration schedule."""
    scheduler = Scheduler()
    media = MediaAsset(path=Path(media_path), duration=300)

    duration = (
        timedelta(seconds=media.duration)
        if media.duration is not None
        else None
    )

    event = ScheduleEvent(
        event_id="demo-program",
        start=datetime.now(UTC),
        duration=duration,
        payload=media,
    )

    scheduler.schedule(event)
    return scheduler


def run_demo(media_path: str | Path) -> None:
    """Run a minimal ChronoPlay playout demonstration."""
    scheduler = create_demo_schedule(media_path)
    engine = PlayoutEngine()

    event = scheduler.pop_next()
    if event is None:
        LOGGER.info("Demo schedule is empty.")
        return

    engine.start()

    try:
        engine.play(event)
        LOGGER.info("Playing demo event: %s", event.event_id)
    finally:
        engine.stop()


def main() -> None:
    """Run the ChronoPlay demonstration."""
    media_path = Path("demo.mp4")

    if not media_path.exists():
        raise FileNotFoundError(f"Demo media file was not found: {media_path}")

    run_demo(media_path)


if __name__ == "__main__":
    main()
