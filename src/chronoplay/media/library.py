from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from uuid import UUID

from chronoplay.media.asset import MediaAsset
from chronoplay.media.source import FileMediaSource
from chronoplay.media.validation import MediaValidationError


class MediaLibrary:
    def __init__(
        self,
        root_or_assets: str | Path | Iterable[MediaAsset] | None = None,
        assets: Iterable[MediaAsset] | None = None,
    ) -> None:
        self.root: Path | None = None
        self._assets: dict[UUID, MediaAsset] = {}
        self._hash_index: dict[str, set[UUID]] = {}

        if isinstance(root_or_assets, (str, Path)):
            normalized_root = str(root_or_assets).strip()
            if not normalized_root:
                raise MediaValidationError("Media library root cannot be empty.")
            self.root = Path(normalized_root)
            asset_iterable = assets
        else:
            asset_iterable = root_or_assets

        if asset_iterable is not None:
            for asset in asset_iterable:
                self.add(asset)

    def resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        if self.root is not None:
            return self.root / p
        return p

    def resolve(self, path: str | Path) -> Path:
        """Alias for resolve_path."""
        return self.resolve_path(path)

    def asset(
        self,
        path: str | Path,
        media_id: str | None = None,
        title: str | None = None,
        duration: float | None = None,
    ) -> MediaAsset:
        resolved = self.resolve_path(path)
        asset_obj = MediaAsset(
            path=resolved,
            media_id=media_id,
            title=title,
            duration=duration,
        )
        self.add(asset_obj)
        return asset_obj

    def validate(
        self,
        path: str | Path,
        media_id: str | None = None,
    ) -> MediaAsset:
        """Resolve, register, and validate an asset, returning the MediaAsset."""
        asset_obj = self.asset(path=path, media_id=media_id)
        asset_obj.validate_path()
        return asset_obj

    def add(self, asset: MediaAsset) -> None:
        if asset.asset_id in self._assets:
            raise ValueError(f"asset already exists: {asset.asset_id}")

        self._assets[asset.asset_id] = asset
        self._index_hash(asset)

    def remove(self, asset_id: UUID) -> MediaAsset:
        try:
            asset = self._assets.pop(asset_id)
        except KeyError as exc:
            raise KeyError(f"asset not found: {asset_id}") from exc

        self._remove_hash_index(asset)
        return asset

    def get(self, asset_id: UUID) -> MediaAsset:
        try:
            return self._assets[asset_id]
        except KeyError as exc:
            raise KeyError(f"asset not found: {asset_id}") from exc

    def find_by_path(self, path: str | Path) -> MediaAsset | None:
        target = Path(path)

        for asset in self._assets.values():
            source = asset.source
            if isinstance(source, FileMediaSource) and source.path == target:
                return asset

        return None

    def find_by_hash(self, content_hash: str) -> tuple[MediaAsset, ...]:
        asset_ids = self._hash_index.get(content_hash, set())
        return tuple(self._assets[asset_id] for asset_id in asset_ids)

    def duplicates(self) -> tuple[tuple[MediaAsset, ...], ...]:
        groups = []

        for asset_ids in self._hash_index.values():
            if len(asset_ids) > 1:
                groups.append(tuple(self._assets[asset_id] for asset_id in asset_ids))

        return tuple(groups)

    def missing(self) -> tuple[MediaAsset, ...]:
        return tuple(asset for asset in self._assets.values() if not asset.available)

    def __contains__(self, asset_id: UUID) -> bool:
        return asset_id in self._assets

    def __len__(self) -> int:
        return len(self._assets)

    def __iter__(self) -> Iterator[MediaAsset]:
        return iter(self._assets.values())

    def _index_hash(self, asset: MediaAsset) -> None:
        if asset.content_hash is None:
            return

        self._hash_index.setdefault(asset.content_hash, set()).add(asset.asset_id)

    def _remove_hash_index(self, asset: MediaAsset) -> None:
        if asset.content_hash is None:
            return

        asset_ids = self._hash_index.get(asset.content_hash)
        if asset_ids is None:
            return

        asset_ids.discard(asset.asset_id)

        if not asset_ids:
            del self._hash_index[asset.content_hash]
