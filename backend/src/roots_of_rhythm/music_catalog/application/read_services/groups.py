from asyncio import gather
from collections.abc import Callable
from typing import TYPE_CHECKING

from roots_of_rhythm.application.transaction import Transaction, TransactionScopeFactory
from roots_of_rhythm.music_catalog.application.ports import (
    ClassificationAssignmentRepository,
    GenreRepository,
    GroupMembershipRepository,
    GroupRepository,
)
from roots_of_rhythm.music_catalog.public.group_reader import GroupOverviewData

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.music_catalog.domain import ClassificationAssignment, Group, GroupMembership

type GroupRepositoryFactory = Callable[[Transaction], GroupRepository]
type AssignmentRepositoryFactory = Callable[[Transaction], ClassificationAssignmentRepository]
type GroupMembershipRepositoryFactory = Callable[[Transaction], GroupMembershipRepository]
type GenreRepositoryFactory = Callable[[Transaction], GenreRepository]


class GroupReadService:
    def __init__(
        self,
        transaction_scope: TransactionScopeFactory,
        group_repository_factory: GroupRepositoryFactory,
        assignment_repository_factory: AssignmentRepositoryFactory,
        group_membership_repository_factory: GroupMembershipRepositoryFactory,
        genre_repository_factory: GenreRepositoryFactory,
    ) -> None:
        self._transaction_scope = transaction_scope
        self._group_repository_factory = group_repository_factory
        self._assignment_repository_factory = assignment_repository_factory
        self._group_membership_repository_factory = group_membership_repository_factory
        self._genre_repository_factory = genre_repository_factory

    async def list_published(self) -> tuple[Group, ...]:
        async with self._transaction_scope() as transaction:
            groups = await self._group_repository_factory(transaction).list_published()
        return tuple(groups)

    async def get_published_by_ids(self, group_ids: Collection[UUID]) -> dict[UUID, Group]:
        if not group_ids:
            return {}
        async with self._transaction_scope() as transaction:
            return await self._group_repository_factory(transaction).get_published_by_ids(group_ids)

    async def get_group_overview(self, group_id: UUID) -> GroupOverviewData:
        async with self._transaction_scope() as transaction:
            group = await self._group_repository_factory(transaction).get_published(group_id)
            if group is None:
                return GroupOverviewData(group=None, assignments=(), genres={}, memberships=())

        assignments, memberships = await gather(
            self._load_assignments(group_id),
            self._load_memberships(group_id),
        )
        genre_ids = {assignment.concept_id for assignment in assignments}
        async with self._transaction_scope() as transaction:
            genres = await self._genre_repository_factory(transaction).get_published_by_ids(genre_ids)
        return GroupOverviewData(group=group, assignments=assignments, genres=genres, memberships=memberships)

    async def _load_assignments(self, group_id: UUID) -> tuple[ClassificationAssignment, ...]:
        async with self._transaction_scope() as transaction:
            assignments = await self._assignment_repository_factory(transaction).list_published_for_group(group_id)
        return tuple(assignments)

    async def _load_memberships(self, group_id: UUID) -> tuple[GroupMembership, ...]:
        async with self._transaction_scope() as transaction:
            memberships = await self._group_membership_repository_factory(transaction).list_published_by_group(group_id)
        return tuple(memberships)
