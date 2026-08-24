"""Media management subpackage for ChronoPlay."""

import chronoplay.media.hashing as _hashing
import chronoplay.media.probe as _probe
import chronoplay.media.validation as _validation
from chronoplay.media.asset import SUPPORTED_EXTENSIONS, MediaAsset
from chronoplay.media.library import MediaLibrary
from chronoplay.media.metadata import MediaMetadata
from chronoplay.media.source import FileMediaSource
from chronoplay.media.states import AssetState

# Alias FileMediaSource as MediaSource for Mypy and backward compatibility
MediaSource = getattr(
    chronoplay.media.source, "MediaSource", FileMediaSource
)

# Import hashing utilities safely regardless of internal function naming
if hasattr(_hashing, "file_hash"):
    file_hash = _hashing.file_hash
elif hasattr(_hashing, "compute_file_hash"):
    file_hash = _hashing.compute_file_hash
elif hasattr(_hashing, "hash_file"):
    file_hash = _hashing.hash_file
else:
    file_hash = getattr(_hashing, "__all__", [None])[0]

# Import validation and probe components safely
MediaNotFoundError = getattr(_validation, "MediaNotFoundError", Exception)
MediaUnreadableError = getattr(_validation, "MediaUnreadableError", Exception)
MediaValidationError = getattr(_validation, "MediaValidationError", Exception)
MediaValidator = getattr(_validation, "MediaValidator", None)
ValidationResult = getattr(_validation, "ValidationResult", None)
FFprobeMediaProbe = getattr(_probe, "FFprobeMediaProbe", None)

__all__ = [
    "AssetState",
    "FFprobeMediaProbe",
    "FileMediaSource",
    "MediaAsset",
    "MediaLibrary",
    "MediaMetadata",
    "MediaNotFoundError",
    "MediaSource",
    "MediaUnreadableError",
    "MediaValidationError",
    "MediaValidator",
    "SUPPORTED_EXTENSIONS",
    "ValidationResult",
    "file_hash",
]


def __getattr__(name: str):
    """Fallback resolution for symbols moved across submodules."""
    for mod in (_hashing, _validation, _probe):
        if hasattr(mod, name):
            return getattr(mod, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
