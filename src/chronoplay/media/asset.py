from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from chronoplay.media.metadata import MediaMetadata
from chronoplay.media.source import FileMediaSource
from chronoplay.media.states import AssetState


@dataclass(slots=True)
class MediaAsset:
    source: FileMediaSource
    asset_id: UUID = field(default_factory=uuid4)
    metadata: MediaMetadata | None = None
    content_hash: str | None = None
    state: AssetState = AssetState.DISCOVERED

    @property
    def available(self) -> bool:
        return self.source.available

    def mark_valid(self, metadata: MediaMetadata, content_hash: str) -> None:
        if not content_hash:
            raise ValueError("content_hash must not be empty")

        self.metadata = metadata
        self.content_hash = content_hash
        self.state = AssetState.VALID

    def mark_invalid(self) -> None:
        self.state = AssetState.INVALID

    def mark_missing(self) -> None:
        self.state = AssetState.MISSING

    def mark_corrupt(self) -> None:
        self.state = AssetState.CORRUPT

    def mark_unavailable(self) -> None:
        self.state = AssetState.UNAVAILABLE

    def mark_validating(self) -> None:
        self.state = AssetState.VALIDATING
