from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class MediaError(Exception):
    """Base exception for media-related errors."""


class MediaValidationError(MediaError, ValueError):
    """Raised when a media asset contains invalid metadata."""


class MediaNotFoundError(MediaError, FileNotFoundError):
    """Raised when a referenced media asset does not exist."""


class MediaUnreadableError(MediaError, OSError):
    """Raised when a media asset cannot be read."""


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


@dataclass(frozen=True, slots=True)
class LegacyMediaAsset:
    path: Path
    media_id: str | None = None
    title: str | None = None
    duration: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
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
        if self.media_id is not None:
            return self.media_id

        return self.path.as_posix()

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @property
    def is_supported(self) -> bool:
        return self.extension in SUPPORTED_MEDIA_EXTENSIONS

    def validate_path(self) -> None:
        if not self.path.exists():
            raise MediaNotFoundError(f"Media asset does not exist: {self.path}")

        if not self.path.is_file():
            raise MediaUnreadableError(
                f"Media path is not a regular file: {self.path}"
            )

        try:
            with self.path.open("rb"):
                pass
        except OSError as exc:
            raise MediaUnreadableError(
                f"Media asset is not readable: {self.path}"
            ) from exc

    def validate(self, *, require_supported_extension: bool = True) -> None:
        self.validate_path()

        if require_supported_extension and not self.is_supported:
            extension = self.extension or "<none>"
            raise MediaValidationError(f"Unsupported media format: {extension}")


@dataclass(frozen=True, slots=True)
class LegacyMediaLibrary:
    root: Path

    def __post_init__(self) -> None:
        root = Path(self.root)

        if not str(root).strip():
            raise MediaValidationError("Media library root cannot be empty.")

        object.__setattr__(self, "root", root)

    def resolve(self, path: str | Path) -> Path:
        media_path = Path(path)

        if media_path.is_absolute():
            return media_path

        return self.root / media_path

    def asset(
        self,
        path: str | Path,
        *,
        media_id: str | None = None,
        title: str | None = None,
        duration: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LegacyMediaAsset:
        return LegacyMediaAsset(
            path=self.resolve(path),
            media_id=media_id,
            title=title,
            duration=duration,
            metadata={} if metadata is None else metadata,
        )

    def validate(self, path: str | Path) -> LegacyMediaAsset:
        asset = self.asset(path)
        asset.validate()
        return asset
