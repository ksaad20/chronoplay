from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class MediaMetadata:
    duration: float
    container: str
    video_codec: str | None = None
    audio_codec: str | None = None
    width: int | None = None
    height: int | None = None
    frame_rate: Fraction | None = None
    audio_channels: int | None = None

    def __post_init__(self) -> None:
        if self.duration < 0:
            raise ValueError("duration must be non-negative")

        if not self.container:
            raise ValueError("container must not be empty")

        if self.width is not None and self.width <= 0:
            raise ValueError("width must be positive")

        if self.height is not None and self.height <= 0:
            raise ValueError("height must be positive")

        if self.frame_rate is not None and self.frame_rate <= 0:
            raise ValueError("frame_rate must be positive")

        if self.audio_channels is not None and self.audio_channels <= 0:
            raise ValueError("audio_channels must be positive")
