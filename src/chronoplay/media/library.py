from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

from chronoplay.media.asset import MediaAsset
from chronoplay.media.source import FileMediaSource


class MediaLibrary:
    def __init__(self, assets: Iterable[MediaAsset] | None = None) -> None:
        self._assets: dict[UUID, MediaAsset] = {}
        self._hash_index: dict[str, set[UUID]] = {}

        if assets is not None:
            for asset in assets:
                self.add(asset)

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
        return tuple(
            asset for asset in self._assets.values() if not asset.available
        )

    def __contains__(self, asset_id: UUID) -> bool:
        return asset_id in self._assets

    def __len__(self) -> int:
        return len(self._assets)

    def __iter__(self):
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
