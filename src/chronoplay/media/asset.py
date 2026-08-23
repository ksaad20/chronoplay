"""Media asset primitives for ChronoPlay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from chronoplay.media.legacy import (
    MediaNotFoundError,
    MediaUnreadableError,
    MediaValidationError,
    SUPPORTED_MEDIA_EXTENSIONS,
)
from chronoplay.media.states import AssetState


@dataclass(frozen=True, slots=True)
class MediaAsset:
    """Represent a media asset used by ChronoPlay."""

    path: Path
    media_id: str | None = None
    title: str | None = None
    duration: float | None = None
    media_metadata: object | None = None
    content_hash: str | None = None
    state: AssetState = AssetState.DISCOVERED

    def __post_init__(self) -> None:
        """Normalize and validate basic asset fields."""
        path = Path(self.path)

        if not str(path).strip():
            raise MediaValidationError("Media path cannot be empty.")

        if self.media_id is not None and not self.media_id.strip():
            raise MediaValidationError("media_id cannot be empty.")

        if self.title is not None and not self.title.strip():
            raise MediaValidationError("title cannot be empty.")

        if self.duration is not None and self.duration < 0:
            raise MediaValidationError("Media duration cannot be negative.")

        object.__setattr__(self, "path", path)

    @property
    def identifier(self) -> str:
        """Return the asset identifier."""
        return self.media_id or self.path.as_posix()

    @property
    def extension(self) -> str:
        """Return the lowercase file extension."""
        return self.path.suffix.lower()

    @property
    def is_supported(self) -> bool:
        """Return whether the file extension is supported."""
        return self.extension in SUPPORTED_MEDIA_EXTENSIONS

    @property
    def available(self) -> bool:
        """Return whether the media file exists."""
        return self.path.is_file()

    def validate(self, *, require_supported_extension: bool = True) -> None:
        """Validate the media asset for playback."""
        if not self.path.exists():
            raise MediaNotFoundError(f"Media asset does not exist: {self.path}")

        if not self.path.is_file():
            raise MediaUnreadableError(
                f"Media path is not a regular file: {self.path}"
            )

        if require_supported_extension and not self.is_supported:
            raise MediaValidationError(
                f"Unsupported media format: {self.extension or '<none>'}"
            )

        try:
            with self.path.open("rb"):
                pass
        except OSError as exc:
            raise MediaUnreadableError(
                f"Media asset is not readable: {self.path}"
            ) from exc
