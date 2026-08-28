from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
from roots_of_rhythm.music_catalog.application.lyrics_body_projection import (
    RIGHTS_RESTRICTED_REASON,
    LyricsBodyDisclosure,
    project_lyrics_version_body,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import LyricsVersion

type MusicUnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]
type HistoricalKnowledgeUnitOfWorkFactory = Callable[[], HistoricalKnowledgeUnitOfWork]


class LyricsVersionProjectionService:
    def __init__(
        self,
        music_uow_factory: MusicUnitOfWorkFactory,
        hk_uow_factory: HistoricalKnowledgeUnitOfWorkFactory,
    ) -> None:
        self._music_uow_factory = music_uow_factory
        self._hk_uow_factory = hk_uow_factory

    async def disclose_body_for_version(self, version: LyricsVersion) -> LyricsBodyDisclosure:
        disclosures = await self.disclose_bodies_for_versions((version,))
        return disclosures[0]

    async def disclose_bodies_for_versions(
        self,
        versions: Sequence[LyricsVersion],
    ) -> list[LyricsBodyDisclosure]:
        if not versions:
            return []
        async with self._hk_uow_factory() as hk:
            source_versions = await hk.sources.get_versions_by_ids(
                [version.source_version_id for version in versions],
            )
            sources = await hk.sources.get_sources_by_ids(
                {source_version.source_id for source_version in source_versions.values()},
            )
        disclosures: list[LyricsBodyDisclosure] = []
        for version in versions:
            source_version = source_versions.get(version.source_version_id)
            if source_version is None:
                disclosures.append(project_lyrics_version_body(version, None))
                continue
            source = sources.get(source_version.source_id)
            policy = None if source is None else source.access_policy
            disclosures.append(project_lyrics_version_body(version, policy))
        return disclosures

    async def disclose_body_for_version_id(self, version_id: UUID) -> LyricsBodyDisclosure:
        async with self._music_uow_factory() as music:
            version = await music.lyrics_versions.get_published(version_id)
            if version is None:
                return LyricsBodyDisclosure(body=None, body_unavailable_reason=RIGHTS_RESTRICTED_REASON)
        return await self.disclose_body_for_version(version)
