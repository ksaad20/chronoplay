from enum import Enum


class AssetState(str, Enum):
    DISCOVERED = "discovered"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    CORRUPT = "corrupt"
    UNAVAILABLE = "unavailable"
