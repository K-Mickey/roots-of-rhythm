from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    LyricsVersionEndpointNotPublished,
    LyricsVersionRelationConflict,
    LyricsVersionRelationNotFound,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import (
    LyricsVersionRelation,
    LyricsVersionRelationContent,
    LyricsVersionRelationType,
)

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class LyricsVersionRelationService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        source_lyrics_version_id: UUID,
        target_lyrics_version_id: UUID,
        relation_type: LyricsVersionRelationType,
        content: LyricsVersionRelationContent | None = None,
        *,
        relation_id: UUID | None = None,
    ) -> LyricsVersionRelation:
        async with self._uow_factory() as uow:
            relation = LyricsVersionRelation.create(
                relation_id or uuid7(),
                source_lyrics_version_id,
                target_lyrics_version_id,
                relation_type,
                content,
            )
            try:
                await uow.lyrics_version_relations.add(relation)
                await uow.commit()
            except UniqueConstraintViolation as error:
                raise LyricsVersionRelationConflict from error
            return relation

    async def replace_content(
        self,
        relation_id: UUID,
        content: LyricsVersionRelationContent,
    ) -> LyricsVersionRelation:
        async with self._uow_factory() as uow:
            relation = await self._get(uow, relation_id, for_update=True)
            updated = relation.replace_content(content)
            try:
                await uow.lyrics_version_relations.save(updated)
                await uow.commit()
            except LookupError as error:
                raise LyricsVersionRelationNotFound(str(relation_id)) from error
            except UniqueConstraintViolation as error:
                raise LyricsVersionRelationConflict from error
            return updated

    async def publish(self, relation_id: UUID) -> LyricsVersionRelation:
        async with self._uow_factory() as uow:
            relation = await self._get(uow, relation_id, for_update=True)
            updated = relation.publish()
            await self._ensure_versions_published(uow, relation)
            try:
                await uow.lyrics_version_relations.save(updated)
                await uow.commit()
            except LookupError as error:
                raise LyricsVersionRelationNotFound(str(relation_id)) from error
            except UniqueConstraintViolation as error:
                raise LyricsVersionRelationConflict from error
            return updated

    async def archive(self, relation_id: UUID) -> LyricsVersionRelation:
        return await self._change_status(relation_id, LyricsVersionRelation.archive)

    async def _change_status(
        self,
        relation_id: UUID,
        transition: Callable[[LyricsVersionRelation], LyricsVersionRelation],
    ) -> LyricsVersionRelation:
        async with self._uow_factory() as uow:
            relation = await self._get(uow, relation_id, for_update=True)
            updated = transition(relation)
            try:
                await uow.lyrics_version_relations.save(updated)
                await uow.commit()
            except LookupError as error:
                raise LyricsVersionRelationNotFound(str(relation_id)) from error
            except UniqueConstraintViolation as error:
                raise LyricsVersionRelationConflict from error
            return updated

    @staticmethod
    async def _ensure_versions_published(uow: MusicCatalogUnitOfWork, relation: LyricsVersionRelation) -> None:
        for version_id in sorted((relation.source_lyrics_version_id, relation.target_lyrics_version_id)):
            if await uow.lyrics_versions.get_published(version_id, for_update=True) is None:
                raise LyricsVersionEndpointNotPublished(str(version_id))

    @staticmethod
    async def _get(
        uow: MusicCatalogUnitOfWork,
        relation_id: UUID,
        *,
        for_update: bool = False,
    ) -> LyricsVersionRelation:
        relation = await uow.lyrics_version_relations.get(relation_id, for_update=for_update)
        if relation is None:
            raise LyricsVersionRelationNotFound(str(relation_id))
        return relation
