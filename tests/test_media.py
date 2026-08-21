from __future__ import annotations

from pathlib import Path

import pytest

from chronoplay.media import (
    MediaAsset,
    MediaLibrary,
    MediaNotFoundError,
    MediaUnreadableError,
    MediaValidationError,
)


def test_media_asset_accepts_valid_asset() -> None:
    """MediaAsset should accept valid media metadata."""
    asset = MediaAsset(
        path=Path("media/news.mp4"),
        media_id="news-001",
        title="Evening News",
        duration=1800.0,
        metadata={"category": "news"},
    )

    assert asset.path == Path("media/news.mp4")
    assert asset.media_id == "news-001"
    assert asset.title == "Evening News"
    assert asset.duration == 1800.0
    assert asset.metadata == {"category": "news"}


def test_media_asset_normalizes_path() -> None:
    """MediaAsset should normalize string paths to Path objects."""
    asset = MediaAsset(path="media/program.mp4")

    assert isinstance(asset.path, Path)
    assert asset.path == Path("media/program.mp4")


def test_media_asset_identifier_uses_media_id() -> None:
    """An explicit media ID should be the asset identifier."""
    asset = MediaAsset(
        path="media/program.mp4",
        media_id="program-001",
    )

    assert asset.identifier == "program-001"


def test_media_asset_identifier_falls_back_to_path() -> None:
    """The path should identify an asset without an explicit media ID."""
    asset = MediaAsset(path="media/program.mp4")

    assert asset.identifier == "media/program.mp4"


def test_media_asset_extension_is_lowercase() -> None:
    """Media extensions should be normalized to lowercase."""
    asset = MediaAsset(path="media/PROGRAM.MP4")

    assert asset.extension == ".mp4"


@pytest.mark.parametrize(
    "extension",
    [
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
    ],
)
def test_supported_media_extensions(extension: str) -> None:
    """Supported media extensions should be recognized."""
    asset = MediaAsset(path=f"media/program{extension}")

    assert asset.is_supported is True


def test_unsupported_media_extension_is_rejected() -> None:
    """Unsupported extensions should not be considered playable."""
    asset = MediaAsset(path="media/program.xyz")

    assert asset.is_supported is False


def test_media_asset_rejects_empty_path() -> None:
    """An empty media path should raise a validation error."""
    with pytest.raises(
        MediaValidationError,
        match="Media path cannot be empty",
    ):
        MediaAsset(path=" ")


def test_media_asset_rejects_empty_media_id() -> None:
    """An empty media ID should raise a validation error."""
    with pytest.raises(
        MediaValidationError,
        match="media_id cannot be empty",
    ):
        MediaAsset(
            path="media/program.mp4",
            media_id=" ",
        )


def test_media_asset_rejects_empty_title() -> None:
    """An empty title should raise a validation error."""
    with pytest.raises(
        MediaValidationError,
        match="title cannot be empty",
    ):
        MediaAsset(
            path="media/program.mp4",
            title=" ",
        )


def test_media_asset_rejects_negative_duration() -> None:
    """Media duration cannot be negative."""
    with pytest.raises(
        MediaValidationError,
        match="Media duration cannot be negative",
    ):
        MediaAsset(
            path="media/program.mp4",
            duration=-1,
        )


def test_media_asset_copies_metadata() -> None:
    """Metadata should not share mutable state with the caller."""
    metadata = {"category": "news"}

    asset = MediaAsset(
        path="media/news.mp4",
        metadata=metadata,
    )

    metadata["category"] = "sports"

    assert asset.metadata == {"category": "news"}


def test_media_asset_validate_path_accepts_readable_file(
    tmp_path: Path,
) -> None:
    """validate_path should accept an existing readable file."""
    media_path = tmp_path / "program.mp4"
    media_path.write_bytes(b"media")

    asset = MediaAsset(path=media_path)

    asset.validate_path()


def test_media_asset_validate_path_rejects_missing_file(
    tmp_path: Path,
) -> None:
    """validate_path should reject missing files."""
    media_path = tmp_path / "missing.mp4"
    asset = MediaAsset(path=media_path)

    with pytest.raises(
        MediaNotFoundError,
        match="Media asset does not exist",
    ):
        asset.validate_path()


def test_media_asset_validate_path_rejects_directory(
    tmp_path: Path,
) -> None:
    """validate_path should reject directories."""
    media_directory = tmp_path / "media.mp4"
    media_directory.mkdir()

    asset = MediaAsset(path=media_directory)

    with pytest.raises(
        MediaUnreadableError,
        match="not a regular file",
    ):
        asset.validate_path()


def test_media_asset_validate_rejects_unsupported_format(
    tmp_path: Path,
) -> None:
    """validate should reject unsupported media formats."""
    media_path = tmp_path / "program.xyz"
    media_path.write_bytes(b"media")

    asset = MediaAsset(path=media_path)

    with pytest.raises(
        MediaValidationError,
        match="Unsupported media format",
    ):
        asset.validate()


def test_media_asset_validate_accepts_supported_file(
    tmp_path: Path,
) -> None:
    """validate should accept an existing supported media file."""
    media_path = tmp_path / "program.mp4"
    media_path.write_bytes(b"media")

    asset = MediaAsset(path=media_path)

    asset.validate()


def test_media_asset_validate_can_skip_extension_check(
    tmp_path: Path,
) -> None:
    """Extension validation should be optional."""
    media_path = tmp_path / "program.custom"
    media_path.write_bytes(b"media")

    asset = MediaAsset(path=media_path)

    asset.validate(require_supported_extension=False)


def test_media_library_normalizes_root(tmp_path: Path) -> None:
    """MediaLibrary should store its root as a Path."""
    library = MediaLibrary(tmp_path)

    assert library.root == tmp_path
    assert isinstance(library.root, Path)


def test_media_library_rejects_empty_root() -> None:
    """MediaLibrary should reject an empty root path."""
    with pytest.raises(
        MediaValidationError,
        match="Media library root cannot be empty",
    ):
        MediaLibrary(" ")


def test_media_library_resolves_relative_path(
    tmp_path: Path,
) -> None:
    """Relative media paths should resolve against the library root."""
    library = MediaLibrary(tmp_path)

    resolved = library.resolve("news/program.mp4")

    assert resolved == tmp_path / "news/program.mp4"


def test_media_library_preserves_absolute_path(
    tmp_path: Path,
) -> None:
    """Absolute media paths should not be joined to the library root."""
    absolute_path = tmp_path / "program.mp4"
    library = MediaLibrary(tmp_path / "media")

    assert library.resolve(absolute_path) == absolute_path


def test_media_library_creates_asset(
    tmp_path: Path,
) -> None:
    """MediaLibrary.asset should create a resolved MediaAsset."""
    library = MediaLibrary(tmp_path)

    asset = library.asset(
        "news/program.mp4",
        media_id="news-001",
        title="News",
        duration=300.0,
    )

    assert asset.path == tmp_path / "news/program.mp4"
    assert asset.media_id == "news-001"
    assert asset.title == "News"
    assert asset.duration == 300.0


def test_media_library_validate(tmp_path: Path) -> None:
    """MediaLibrary.validate should resolve and validate an asset."""
    media_path = tmp_path / "program.mp4"
    media_path.write_bytes(b"media")

    library = MediaLibrary(tmp_path)

    asset = library.validate("program.mp4")

    assert asset.path == media_path
    assert asset.is_supported is True
