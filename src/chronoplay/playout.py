from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from chronoplay.media.asset import MediaAsset
from chronoplay.media.validation import MediaError

if TYPE_CHECKING:
    from chronoplay.scheduler import ScheduleEvent


class PlayoutState(Enum):
    STOPPED = auto()
    READY = auto()
    PLAYING = auto()
    ERROR = auto()


class PlayoutError(Exception):
    """Base exception for playout errors."""


@dataclass(frozen=True)
class PlayoutResult:
    event_id: str
    media_id: str
    media_path: str
    state: PlayoutState


class PlayoutEngine:
    def __init__(
        self,
        validator: Callable[[MediaAsset], None] | None = None,
    ) -> None:
        self._state: PlayoutState = PlayoutState.STOPPED
        self._current_event: ScheduleEvent | None = None
        self._validator = validator

    @property
    def state(self) -> PlayoutState:
        return self._state

    @property
    def current_event(self) -> ScheduleEvent | None:
        return self._current_event

    def start(self) -> None:
        if self._state in (PlayoutState.STOPPED, PlayoutState.READY):
            self._state = PlayoutState.READY

    def stop(self) -> None:
        self._current_event = None
        self._state = PlayoutState.STOPPED

    def reset(self) -> None:
        self.stop()

    def play(self, event: ScheduleEvent) -> PlayoutResult:
        if self._state is PlayoutState.STOPPED:
            raise PlayoutError("Engine must be started before playing")

        if self._state is PlayoutState.ERROR:
            raise PlayoutError("Engine is in an error state")

        if not isinstance(event.payload, MediaAsset):
            raise PlayoutError("Schedule event payload must contain a MediaAsset")

        asset: MediaAsset = event.payload

        if self._validator is not None:
            try:
                self._validator(asset)
            except MediaError as exc:
                self._state = PlayoutState.ERROR
                self._current_event = None
                raise PlayoutError("Media validation failed") from exc
            except Exception:
                self._current_event = None
                raise
        else:
            try:
                asset.validate()
            except MediaError as exc:
                self._state = PlayoutState.ERROR
                self._current_event = None
                raise PlayoutError("Media validation failed") from exc

        self._current_event = event
        self._state = PlayoutState.PLAYING

        return PlayoutResult(
            event_id=str(event.event_id),
            media_id=asset.identifier,
            media_path=str(asset.path),
            state=self._state,
        )

    def complete(self) -> PlayoutResult | None:
        if self._current_event is None or self._state is not PlayoutState.PLAYING:
            return None

        event = self._current_event
        asset: MediaAsset = event.payload

        self._state = PlayoutState.READY
        self._current_event = None

        return PlayoutResult(
            event_id=str(event.event_id),
            media_id=asset.identifier,
            media_path=str(asset.path),
            state=self._state,
        )
