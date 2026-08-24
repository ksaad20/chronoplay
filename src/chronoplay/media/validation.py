from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from chronoplay.media.asset import MediaAsset

from chronoplay.media.hashing import hash_file
from chronoplay.media.metadata import MediaMetadata
from chronoplay.media.probe import MediaProbeError
from chronoplay.media.source import FileMediaSource
from chronoplay.media.states import AssetState


class MediaValidationError(Exception):
    """Base exception for media validation and processing errors."""

    pass


# Alias for backward compatibility across modules
MediaError = MediaValidationError


class MediaValidationFailure(MediaValidationError):
    """Raised when media validation fails."""

    pass


class MediaNotFoundError(MediaValidationError):
    """Raised when a requested media asset cannot be found."""

    pass


class MediaUnreadableError(MediaValidationError):
    """Raised when a media asset cannot be read or processed."""

    pass


class MediaProbe(Protocol):
    def probe(self, path: str | Path) -> MediaMetadata: ...


@dataclass(frozen=True, slots=True)
class ValidationResult:
    state: AssetState
    metadata: MediaMetadata | None = None
    content_hash: str | None = None
    error: str | None = None

    @property
    def valid(self) -> bool:
        return self.state is AssetState.VALID


class MediaValidator:
    def __init__(self, probe: MediaProbe) -> None:
        self.probe = probe

    def validate(self, asset: MediaAsset) -> ValidationResult:
        asset.mark_validating()

        source = asset.source

        if not isinstance(source, FileMediaSource):
            asset.mark_unavailable()
            return ValidationResult(
                state=AssetState.UNAVAILABLE,
                error="unsupported media source",
            )

        if not source.available:
            asset.mark_missing()
            return ValidationResult(
                state=AssetState.MISSING,
                error=f"media file does not exist: {source.path}",
            )

        try:
            metadata = self.probe.probe(source.path)
            content_hash = hash_file(source.path)
        except (MediaProbeError, OSError, ValueError) as exc:
            asset.mark_corrupt()
            return ValidationResult(
                state=AssetState.CORRUPT,
                error=str(exc),
            )

        asset.mark_valid(metadata, content_hash)

        return ValidationResult(
            state=AssetState.VALID,
            metadata=metadata,
            content_hash=content_hash,
        )
