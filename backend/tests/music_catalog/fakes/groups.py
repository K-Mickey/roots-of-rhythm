from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import Group, GroupMembership


class FakeGroupRepository:
    def __init__(self, groups: dict[UUID, Group]) -> None:
        self._groups = groups
        self.locked_ids: list[UUID] = []
        self.batch_calls: list[tuple[UUID, ...]] = []

    async def add(self, group: Group) -> None:
        self._groups[group.id] = group

    async def get(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        return self._groups.get(group_id)

    async def get_published(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        group = self._groups.get(group_id)
        return group if group is not None and group.is_published else None

    async def get_published_by_ids(self, group_ids: Collection[UUID], *, for_update: bool = False) -> dict[UUID, Group]:
        ids = sorted(set(group_ids))
        self.batch_calls.append(tuple(ids))
        if for_update:
            self.locked_ids.extend(ids)
        return {
            group_id: group
            for group_id in ids
            if (group := self._groups.get(group_id)) is not None and group.is_published
        }

    async def list_published(self) -> list[Group]:
        return sorted(
            (group for group in self._groups.values() if group.is_published),
            key=lambda group: group.canonical_name,
        )

    async def save(self, group: Group) -> None:
        if group.id not in self._groups:
            raise LookupError(str(group.id))
        self._groups[group.id] = group

    async def mark_deleted(self, group_id: UUID) -> None:
        self._groups.pop(group_id, None)


class FakeGroupMembershipRepository:
    def __init__(self, memberships: dict[UUID, GroupMembership]) -> None:
        self._memberships = memberships

    async def add(self, membership: GroupMembership) -> None:
        self._memberships[membership.id] = membership

    async def get(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        return self._memberships.get(membership_id)

    async def get_published(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        membership = self._memberships.get(membership_id)
        if membership is None or not membership.is_published:
            return None
        return membership

    async def list_published_by_group(self, group_id: UUID) -> list[GroupMembership]:
        return sorted(
            (
                membership
                for membership in self._memberships.values()
                if membership.group_id == group_id and membership.is_published
            ),
            key=lambda membership: membership.id,
        )

    async def save(self, membership: GroupMembership) -> None:
        if membership.id not in self._memberships:
            raise LookupError(str(membership.id))
        self._memberships[membership.id] = membership

    async def mark_deleted(self, membership_id: UUID) -> None:
        self._memberships.pop(membership_id, None)
