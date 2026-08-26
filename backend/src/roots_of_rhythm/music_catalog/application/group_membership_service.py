from collections.abc import Callable
from uuid import UUID, uuid7

from roots_of_rhythm.music_catalog.application.errors import GroupMembershipNotFound
from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
from roots_of_rhythm.music_catalog.domain import GroupMembership, GroupMembershipContent

type UnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


class GroupMembershipService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create(
        self,
        person_id: UUID,
        group_id: UUID,
        content: GroupMembershipContent | None = None,
        *,
        membership_id: UUID | None = None,
    ) -> GroupMembership:
        async with self._uow_factory() as uow:
            membership = GroupMembership.create(
                membership_id or uuid7(),
                person_id,
                group_id,
                content,
            )
            await uow.group_memberships.add(membership)
            await uow.commit()
            return membership

    async def replace_content(self, membership_id: UUID, content: GroupMembershipContent) -> GroupMembership:
        async with self._uow_factory() as uow:
            membership = await self._get(uow, membership_id, for_update=True)
            updated = membership.replace_content(content)
            try:
                await uow.group_memberships.save(updated)
            except LookupError as error:
                raise GroupMembershipNotFound(str(membership_id)) from error
            await uow.commit()
            return updated

    async def publish(self, membership_id: UUID) -> GroupMembership:
        return await self._change_status(membership_id, GroupMembership.publish)

    async def archive(self, membership_id: UUID) -> GroupMembership:
        return await self._change_status(membership_id, GroupMembership.archive)

    async def _change_status(
        self,
        membership_id: UUID,
        transition: Callable[[GroupMembership], GroupMembership],
    ) -> GroupMembership:
        async with self._uow_factory() as uow:
            membership = await self._get(uow, membership_id, for_update=True)
            updated = transition(membership)
            try:
                await uow.group_memberships.save(updated)
            except LookupError as error:
                raise GroupMembershipNotFound(str(membership_id)) from error
            await uow.commit()
            return updated

    @staticmethod
    async def _get(
        uow: MusicCatalogUnitOfWork,
        membership_id: UUID,
        *,
        for_update: bool = False,
    ) -> GroupMembership:
        membership = await uow.group_memberships.get(membership_id, for_update=for_update)
        if membership is None:
            raise GroupMembershipNotFound(str(membership_id))
        return membership
