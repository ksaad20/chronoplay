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
    delegated to future backend implementations.
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
        """Validate a media asset before playout."""
        if not asset.path.exists():
            raise MediaError(f"Media asset does not exist: {asset.path}")

        if not asset.path.is_file():
            raise MediaError(
                f"Media path is not a regular file: {asset.path}"
            )

        if not asset.is_supported:
            raise MediaError(
                f"Unsupported media format: "
                f"{asset.path.suffix.lower() or '<none>'}"
            )

        try:
            with asset.path.open("rb"):
                pass
        except OSError as exc:
            raise MediaError(
                f"Media asset is not readable: {asset.path}"
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
            raise PlayoutError("ScheduleEvent payload must contain a MediaAsset.")

        return payload
