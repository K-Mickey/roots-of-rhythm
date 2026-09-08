from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import GroupNotFound
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import Group, GroupContent

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class GroupService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(self, content: GroupContent, *, group_id: UUID | None = None) -> Group:
        async with self._uow_factory() as uow:
            group = Group.create(group_id or uuid7(), content)
            await uow.groups.add(group)
            await uow.commit()
            return group

    async def replace_content(self, group_id: UUID, content: GroupContent) -> Group:
        async with self._uow_factory() as uow:
            group = await self._get(uow, group_id, for_update=True)
            updated = group.replace_content(content)
            try:
                await uow.groups.save(updated)
            except LookupError as error:
                raise GroupNotFound(str(group_id)) from error
            await uow.commit()
            return updated

    async def publish(self, group_id: UUID) -> Group:
        return await self._change_status(group_id, Group.publish)

    async def archive(self, group_id: UUID) -> Group:
        return await self._change_status(group_id, Group.archive)

    async def _change_status(self, group_id: UUID, transition: Callable[[Group], Group]) -> Group:
        async with self._uow_factory() as uow:
            group = await self._get(uow, group_id, for_update=True)
            updated = transition(group)
            try:
                await uow.groups.save(updated)
            except LookupError as error:
                raise GroupNotFound(str(group_id)) from error
            await uow.commit()
            return updated

    @staticmethod
    async def _get(uow: MusicCatalogUnitOfWork, group_id: UUID, *, for_update: bool = False) -> Group:
        group = await uow.groups.get(group_id, for_update=for_update)
        if group is None:
            raise GroupNotFound(str(group_id))
        return group
