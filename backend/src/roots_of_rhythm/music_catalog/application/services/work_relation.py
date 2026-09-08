from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import (
    UniqueConstraintViolation,
    WorkRelationConflict,
    WorkRelationNotFound,
    WorkRelationWorkNotPublished,
)
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import EvidenceStatus, WorkRelation, WorkRelationContent, WorkRelationType

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class WorkRelationService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        source_work_id: UUID,
        target_work_id: UUID,
        relation_type: WorkRelationType,
        content: WorkRelationContent | None = None,
        *,
        evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED,
        relation_id: UUID | None = None,
    ) -> WorkRelation:
        async with self._uow_factory() as uow:
            relation = WorkRelation.create(
                relation_id or uuid7(),
                source_work_id,
                target_work_id,
                relation_type,
                content,
                evidence_status=evidence_status,
            )
            try:
                await uow.work_relations.add(relation)
                await uow.commit()
            except UniqueConstraintViolation as error:
                raise WorkRelationConflict from error
            return relation

    async def replace_content(
        self,
        relation_id: UUID,
        content: WorkRelationContent,
        *,
        evidence_status: EvidenceStatus | None = None,
    ) -> WorkRelation:
        async with self._uow_factory() as uow:
            relation = await self._get(uow, relation_id, for_update=True)
            updated = relation.replace_content(content, evidence_status=evidence_status)
            try:
                await uow.work_relations.save(updated)
                await uow.commit()
            except LookupError as error:
                raise WorkRelationNotFound(str(relation_id)) from error
            except UniqueConstraintViolation as error:
                raise WorkRelationConflict from error
            return updated

    async def publish(self, relation_id: UUID) -> WorkRelation:
        async with self._uow_factory() as uow:
            relation = await self._get(uow, relation_id, for_update=True)
            updated = relation.publish()
            await self._ensure_works_published(uow, relation)
            try:
                await uow.work_relations.save(updated)
                await uow.commit()
            except LookupError as error:
                raise WorkRelationNotFound(str(relation_id)) from error
            except UniqueConstraintViolation as error:
                raise WorkRelationConflict from error
            return updated

    async def archive(self, relation_id: UUID) -> WorkRelation:
        return await self._change_status(relation_id, WorkRelation.archive)

    async def _change_status(
        self,
        relation_id: UUID,
        transition: Callable[[WorkRelation], WorkRelation],
    ) -> WorkRelation:
        async with self._uow_factory() as uow:
            relation = await self._get(uow, relation_id, for_update=True)
            updated = transition(relation)
            try:
                await uow.work_relations.save(updated)
                await uow.commit()
            except LookupError as error:
                raise WorkRelationNotFound(str(relation_id)) from error
            except UniqueConstraintViolation as error:
                raise WorkRelationConflict from error
            return updated

    @staticmethod
    async def _ensure_works_published(uow: MusicCatalogUnitOfWork, relation: WorkRelation) -> None:
        for work_id in sorted((relation.source_work_id, relation.target_work_id)):
            if await uow.works.get_published(work_id, for_update=True) is None:
                raise WorkRelationWorkNotPublished(str(work_id))

    @staticmethod
    async def _get(
        uow: MusicCatalogUnitOfWork,
        relation_id: UUID,
        *,
        for_update: bool = False,
    ) -> WorkRelation:
        relation = await uow.work_relations.get(relation_id, for_update=for_update)
        if relation is None:
            raise WorkRelationNotFound(str(relation_id))
        return relation
