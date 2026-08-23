from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from chronoplay.media.metadata import MediaMetadata
from chronoplay.media.source import FileMediaSource
from chronoplay.media.states import AssetState


SUPPORTED_MEDIA_EXTENSIONS = frozenset(
    {
        ".avi",
        ".m4a",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp3",
        ".mp4",
        ".mpeg",
        ".mpg",
        ".ts",
        ".wav",
        ".webm",
    }
)


class MediaError(Exception):
    """Base exception for media-related errors."""


class MediaValidationError(MediaError, ValueError):
    """Raised when media validation fails."""


class MediaNotFoundError(MediaError, FileNotFoundError):
    """Raised when a media asset does not exist."""


class MediaUnreadableError(MediaError, OSError):
    """Raised when a media asset cannot be read."""


@dataclass(slots=True)
class MediaAsset:
    """Represent a media asset and its lifecycle state."""

    path: Path
    media_id: str | None = None
    title: str | None = None
    duration: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    asset_id: UUID = field(default_factory=uuid4)
    media_metadata: MediaMetadata | None = None
    content_hash: str | None = None
    state: AssetState = AssetState.DISCOVERED

    def __post_init__(self) -> None:
        """Normalize and validate construction-time values."""
        normalized_path = Path(self.path)

        if not str(normalized_path).strip():
            raise MediaValidationError("Media path cannot be empty.")

        if self.media_id is not None and not self.media_id.strip():
            raise MediaValidationError("media_id cannot be empty.")

        if self.title is not None and not self.title.strip():
            raise MediaValidationError("title cannot be empty.")

        if self.duration is not None and self.duration < 0:
            raise MediaValidationError("Media duration cannot be negative.")

        object.__setattr__(self, "path", normalized_path)
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def identifier(self) -> str:
        """Return the stable public identifier for the asset."""
        if self.media_id is not None:
            return self.media_id

        return str(self.asset_id)

    @property
    def extension(self) -> str:
        """Return the normalized file extension."""
        return self.path.suffix.lower()

    @property
    def is_supported(self) -> bool:
        """Return whether the asset uses a supported media extension."""
        return self.extension in SUPPORTED_MEDIA_EXTENSIONS

    @property
    def source(self) -> FileMediaSource:
        """Return the file-backed media source."""
        return FileMediaSource(self.path)

    @property
    def available(self) -> bool:
        """Return whether the referenced media file is available."""
        return self.path.exists() and self.path.is_file()

    def validate_path(self) -> None:
        """Validate that the media path exists and is readable."""
        if not self.path.exists():
            raise MediaNotFoundError(f"Media asset does not exist: {self.path}")

        if not self.path.is_file():
            raise MediaUnreadableError(f"Media path is not a regular file: {self.path}")

        try:
            with self.path.open("rb"):
                pass
        except OSError as exc:
            raise MediaUnreadableError(
                f"Media asset is not readable: {self.path}"
            ) from exc

    def validate(self, *, require_supported_extension: bool = True) -> None:
        """Validate the asset for use by ChronoPlay."""
        self.validate_path()

        if require_supported_extension and not self.is_supported:
            extension = self.extension or "<none>"
            raise MediaValidationError(f"Unsupported media format: {extension}")

    def mark_validating(self) -> None:
        """Move the asset into the validation state."""
        self.state = AssetState.VALIDATING

    def mark_valid(
        self,
        metadata: MediaMetadata,
        content_hash: str,
    ) -> None:
        """Store validated metadata and mark the asset valid."""
        if not content_hash:
            raise ValueError("content_hash must not be empty")

        self.media_metadata = metadata
        self.content_hash = content_hash
        self.duration = metadata.duration
        self.state = AssetState.VALID

    def mark_invalid(self) -> None:
        """Mark the asset as invalid."""
        self.state = AssetState.INVALID

    def mark_missing(self) -> None:
        """Mark the asset as missing."""
        self.state = AssetState.MISSING

    def mark_corrupt(self) -> None:
        """Mark the asset as corrupt."""
        self.state = AssetState.CORRUPT

    def mark_unavailable(self) -> None:
        """Mark the asset as unavailable."""
        self.state = AssetState.UNAVAILABLE
