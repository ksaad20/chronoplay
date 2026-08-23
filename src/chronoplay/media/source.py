from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileMediaSource:
    path: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))

    @property
    def available(self) -> bool:
        return self.path.is_file()
