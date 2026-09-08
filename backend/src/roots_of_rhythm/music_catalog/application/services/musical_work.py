from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import MusicalWorkNotFound
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import MusicalWork, WorkContent

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class MusicalWorkService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(self, content: WorkContent, *, work_id: UUID | None = None) -> MusicalWork:
        async with self._uow_factory() as uow:
            work = MusicalWork.create(work_id or uuid7(), content)
            await uow.works.add(work)
            await uow.commit()
            return work

    async def replace_content(self, work_id: UUID, content: WorkContent) -> MusicalWork:
        async with self._uow_factory() as uow:
            work = await self._get(uow, work_id, for_update=True)
            updated = work.replace_content(content)
            try:
                await uow.works.save(updated)
            except LookupError as error:
                raise MusicalWorkNotFound(str(work_id)) from error
            await uow.commit()
            return updated

    async def publish(self, work_id: UUID) -> MusicalWork:
        return await self._change_status(work_id, MusicalWork.publish)

    async def archive(self, work_id: UUID) -> MusicalWork:
        return await self._change_status(work_id, MusicalWork.archive)

    async def _change_status(self, work_id: UUID, transition: Callable[[MusicalWork], MusicalWork]) -> MusicalWork:
        async with self._uow_factory() as uow:
            work = await self._get(uow, work_id, for_update=True)
            updated = transition(work)
            try:
                await uow.works.save(updated)
            except LookupError as error:
                raise MusicalWorkNotFound(str(work_id)) from error
            await uow.commit()
            return updated

    @staticmethod
    async def _get(uow: MusicCatalogUnitOfWork, work_id: UUID, *, for_update: bool = False) -> MusicalWork:
        work = await uow.works.get(work_id, for_update=for_update)
        if work is None:
            raise MusicalWorkNotFound(str(work_id))
        return work
