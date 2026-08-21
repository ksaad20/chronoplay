from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Any

from chronoplay.media import MediaAsset, MediaError
from chronoplay.scheduler import ScheduleEvent

class PlayoutError(Exception):
    """Base exception for playout-related errors."""


class PlayoutState(str, Enum):
    """States supported by the v0.0.1 playout engine."""

    STOPPED = "stopped"
    READY = "ready"
    PLAYING = "playing"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class PlayoutResult:
    """Result produced when a media event is accepted for playout."""

    event_id: str
    media_id: str
    media_path: str
    state: PlayoutState


class PlayoutEngine:
    """Backend-independent media playout controller.

    The v0.0.1 engine validates media and manages deterministic playout
    state. Actual decoding, rendering, encoding, and network delivery are
    intentionally delegated to future backend implementations.
    """

    def __init__(
        self,
        *,
        validator: Callable[[MediaAsset], None] | None = None,
    ) -> None:
        """Initialize the playout engine."""
        self._validator = validator or self._default_validator
        self._state = PlayoutState.STOPPED
        self._current_event: ScheduleEvent | None = None
        self._lock = RLock()

    @staticmethod
    def _default_validator(asset: MediaAsset) -> None:
        """Validate a media asset using its built-in validation rules."""
        asset.validate()

    @property
    def state(self) -> PlayoutState:
        """Return the current playout state."""
        with self._lock:
            return self._state

    @property
    def current_event(self) -> ScheduleEvent | None:
        """Return the event currently assigned to playout."""
        with self._lock:
            return self._current_event

    def start(self) -> None:
        """Prepare the playout engine for media execution."""
        with self._lock:
            if self._state is PlayoutState.PLAYING:
                raise PlayoutError("Playout engine is already playing.")

            if self._state is PlayoutState.ERROR:
                raise PlayoutError(
                    "Playout engine is in an error state."
                )

            self._state = PlayoutState.READY

    def stop(self) -> None:
        """Stop playout and clear the current event."""
        with self._lock:
            self._current_event = None
            self._state = PlayoutState.STOPPED

    def play(self, event: ScheduleEvent) -> PlayoutResult:
        """Validate and accept a scheduled event for playout."""
        with self._lock:
            if self._state is PlayoutState.STOPPED:
                raise PlayoutError(
                    "Playout engine must be started before playing an event."
                )

            if self._state is PlayoutState.ERROR:
                raise PlayoutError(
                    "Playout engine is in an error state."
                )

            media = self._extract_media(event)

            try:
                self._validator(media)
            except MediaError as exc:
                self._state = PlayoutState.ERROR
                self._current_event = None
                raise PlayoutError(
                    f"Media validation failed for event {event.event_id}: "
                    f"{exc}"
                ) from exc

            self._current_event = event
            self._state = PlayoutState.PLAYING

            return PlayoutResult(
                event_id=event.event_id,
                media_id=media.identifier,
                media_path=str(media.path),
                state=self._state,
            )

    def complete(self) -> PlayoutResult | None:
        """Mark the current event as completed."""
        with self._lock:
            if self._current_event is None:
                return None

            event = self._current_event
            media = self._extract_media(event)

            result = PlayoutResult(
                event_id=event.event_id,
                media_id=media.identifier,
                media_path=str(media.path),
                state=PlayoutState.READY,
            )

            self._current_event = None
            self._state = PlayoutState.READY

            return result

    def reset(self) -> None:
        """Recover an errored engine and return it to the stopped state."""
        with self._lock:
            self._current_event = None
            self._state = PlayoutState.STOPPED

    @staticmethod
    def _extract_media(event: ScheduleEvent) -> MediaAsset:
        """Extract a MediaAsset from a scheduled event payload."""
        payload: Any = event.payload

        if not isinstance(payload, MediaAsset):
            raise PlayoutError(
                "ScheduleEvent payload must contain a MediaAsset."
            )

        return payload
