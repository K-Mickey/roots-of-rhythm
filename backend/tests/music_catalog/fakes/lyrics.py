from typing import TYPE_CHECKING

from roots_of_rhythm.music_catalog.domain import LyricsUsageKind

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import (
        LyricsVersion,
        LyricsVersionCredit,
        LyricsVersionRelation,
    )


class FakeLyricsVersionRepository:
    def __init__(self, versions: dict[UUID, LyricsVersion]) -> None:
        self._versions = versions
        self.locked_ids: list[UUID] = []
        self.batch_calls: list[tuple[UUID, ...]] = []

    async def add(self, version: LyricsVersion) -> None:
        self._versions[version.id] = version

    async def get(self, version_id: UUID, *, for_update: bool = False) -> LyricsVersion | None:
        return self._versions.get(version_id)

    async def get_published(self, version_id: UUID, *, for_update: bool = False) -> LyricsVersion | None:
        version = self._versions.get(version_id)
        return version if version is not None and version.is_published else None

    async def get_published_by_ids(
        self, version_ids: Collection[UUID], *, for_update: bool = False
    ) -> dict[UUID, LyricsVersion]:
        ids = sorted(set(version_ids))
        self.batch_calls.append(tuple(ids))
        if for_update:
            self.locked_ids.extend(ids)
        return {
            version_id: version
            for version_id in ids
            if (version := self._versions.get(version_id)) is not None and version.is_published
        }

    async def list_published_for_work(self, work_id: UUID) -> list[LyricsVersion]:
        return (await self.list_published_for_works([work_id])).get(work_id, [])

    async def list_published_for_works(self, work_ids: Collection[UUID]) -> dict[UUID, list[LyricsVersion]]:
        usage_rank = {LyricsUsageKind.PERFORMABLE: 0, LyricsUsageKind.READING_TRANSLATION: 1}
        ids = set(work_ids)
        versions: dict[UUID, list[LyricsVersion]] = {}
        for version in sorted(
            (version for version in self._versions.values() if version.work_id in ids and version.is_published),
            key=lambda version: (
                version.work_id,
                usage_rank[version.usage_kind],
                version.language_tag,
                version.label or "",
                version.id,
            ),
        ):
            versions.setdefault(version.work_id, []).append(version)
        return versions

    async def save(self, version: LyricsVersion) -> None:
        if version.id not in self._versions:
            raise LookupError(str(version.id))
        self._versions[version.id] = version

    async def mark_deleted(self, version_id: UUID) -> None:
        self._versions.pop(version_id, None)


class FakeLyricsVersionCreditRepository:
    def __init__(self, version_credits: dict[UUID, LyricsVersionCredit]) -> None:
        self._credits = version_credits

    async def add(self, credit: LyricsVersionCredit) -> None:
        self._credits[credit.id] = credit

    async def get(self, credit_id: UUID, *, for_update: bool = False) -> LyricsVersionCredit | None:
        return self._credits.get(credit_id)

    async def get_published(self, credit_id: UUID, *, for_update: bool = False) -> LyricsVersionCredit | None:
        credit = self._credits.get(credit_id)
        return credit if credit is not None and credit.is_published else None

    async def list_published_for_version(self, lyrics_version_id: UUID) -> list[LyricsVersionCredit]:
        return sorted(
            (
                credit
                for credit in self._credits.values()
                if credit.lyrics_version_id == lyrics_version_id and credit.is_published
            ),
            key=lambda credit: (credit.role.value, credit.id),
        )

    async def list_published_for_versions(
        self,
        lyrics_version_ids: Collection[UUID],
    ) -> dict[UUID, list[LyricsVersionCredit]]:
        ids = set(lyrics_version_ids)
        return {version_id: await self.list_published_for_version(version_id) for version_id in ids}

    async def save(self, credit: LyricsVersionCredit) -> None:
        if credit.id not in self._credits:
            raise LookupError(str(credit.id))
        self._credits[credit.id] = credit

    async def mark_deleted(self, credit_id: UUID) -> None:
        self._credits.pop(credit_id, None)


class FakeLyricsVersionRelationRepository:
    def __init__(self, relations: dict[UUID, LyricsVersionRelation]) -> None:
        self._relations = relations

    async def add(self, relation: LyricsVersionRelation) -> None:
        self._relations[relation.id] = relation

    async def get(self, relation_id: UUID, *, for_update: bool = False) -> LyricsVersionRelation | None:
        return self._relations.get(relation_id)

    async def get_published(self, relation_id: UUID, *, for_update: bool = False) -> LyricsVersionRelation | None:
        relation = self._relations.get(relation_id)
        if relation is None or not relation.is_published:
            return None
        return relation

    async def list_published_for_version(self, lyrics_version_id: UUID) -> list[LyricsVersionRelation]:
        return sorted(
            (
                relation
                for relation in self._relations.values()
                if relation.is_published
                and (
                    relation.source_lyrics_version_id == lyrics_version_id
                    or relation.target_lyrics_version_id == lyrics_version_id
                )
            ),
            key=lambda relation: (relation.relation_type.value, relation.id),
        )

    async def list_published_for_versions(
        self,
        lyrics_version_ids: Collection[UUID],
    ) -> dict[UUID, list[LyricsVersionRelation]]:
        ids = set(lyrics_version_ids)
        return {version_id: await self.list_published_for_version(version_id) for version_id in ids}

    async def save(self, relation: LyricsVersionRelation) -> None:
        if relation.id not in self._relations:
            raise LookupError(str(relation.id))
        self._relations[relation.id] = relation

    async def mark_deleted(self, relation_id: UUID) -> None:
        self._relations.pop(relation_id, None)
