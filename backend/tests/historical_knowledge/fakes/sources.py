from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import Source, SourceFragment, SourceVersion


class FakeSourceRepository:
    def __init__(self) -> None:
        self.sources: dict[UUID, Source] = {}
        self.versions: dict[UUID, SourceVersion] = {}
        self.fragments: dict[UUID, SourceFragment] = {}

    async def add_source(self, source: Source) -> None:
        self.sources[source.id] = source

    async def save_source(self, source: Source) -> None:
        self.sources[source.id] = source

    async def add_version(self, version: SourceVersion) -> None:
        self.versions[version.id] = version

    async def add_fragment(self, fragment: SourceFragment) -> None:
        self.fragments[fragment.id] = fragment

    async def get_source(self, source_id: UUID, *, for_update: bool = False) -> Source | None:
        return self.sources.get(source_id)

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        return {source_id: source for source_id in source_ids if (source := self.sources.get(source_id)) is not None}

    async def get_version(self, version_id: UUID, *, for_update: bool = False) -> SourceVersion | None:
        return self.versions.get(version_id)

    async def get_versions_by_ids(self, version_ids: Collection[UUID]) -> dict[UUID, SourceVersion]:
        return {
            version_id: version for version_id in version_ids if (version := self.versions.get(version_id)) is not None
        }

    async def get_fragment(self, fragment_id: UUID, *, for_update: bool = False) -> SourceFragment | None:
        return self.fragments.get(fragment_id)

    async def get_fragments_by_ids(
        self,
        fragment_ids: Collection[UUID],
        *,
        for_update: bool = False,
    ) -> dict[UUID, SourceFragment]:
        return {
            fragment_id: fragment
            for fragment_id in fragment_ids
            if (fragment := self.fragments.get(fragment_id)) is not None
        }

    async def save_fragment(self, fragment: SourceFragment) -> None:
        self.fragments[fragment.id] = fragment

    async def mark_source_deleted(self, source_id: UUID) -> None:
        self.sources.pop(source_id, None)
        version_ids = [version.id for version in self.versions.values() if version.source_id == source_id]
        for version_id in version_ids:
            self.versions.pop(version_id, None)
        for fragment_id, fragment in list(self.fragments.items()):
            if fragment.source_version_id in version_ids:
                self.fragments.pop(fragment_id, None)

    async def mark_version_deleted(self, version_id: UUID) -> None:
        self.versions.pop(version_id, None)
        for fragment_id, fragment in list(self.fragments.items()):
            if fragment.source_version_id == version_id:
                self.fragments.pop(fragment_id, None)

    async def mark_fragment_deleted(self, fragment_id: UUID) -> None:
        self.fragments.pop(fragment_id, None)

    async def reviewed_source_ids_for_fragments(self, fragment_ids: Collection[UUID]) -> dict[UUID, UUID]:
        result: dict[UUID, UUID] = {}
        for fragment_id in fragment_ids:
            fragment = self.fragments.get(fragment_id)
            if fragment is None or not fragment.is_reviewed:
                continue
            version = self.versions.get(fragment.source_version_id)
            if version is None:
                continue
            result[fragment_id] = version.source_id
        return result
