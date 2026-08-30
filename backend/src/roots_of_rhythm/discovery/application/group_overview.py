from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto import (
    GenreSummary,
    GroupMemberView,
    GroupOverviewResponse,
    GroupPeriodView,
)
from roots_of_rhythm.discovery.application.errors import GroupOverviewNotFound

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork

type PeopleUnitOfWorkFactory = Callable[[], PeopleCatalogUnitOfWork]
type MusicUnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class GroupOverviewReader(Protocol):
    async def get(self, group_id: UUID) -> GroupOverviewResponse: ...


class GroupOverviewQuery:
    def __init__(
        self,
        music_uow_factory: MusicUnitOfWorkFactory,
        people_uow_factory: PeopleUnitOfWorkFactory,
    ) -> None:
        self._music_uow_factory = music_uow_factory
        self._people_uow_factory = people_uow_factory

    async def get(self, group_id: UUID) -> GroupOverviewResponse:
        async with self._music_uow_factory() as music_uow:
            group = await music_uow.groups.get_published(group_id)
            if group is None:
                raise GroupOverviewNotFound(str(group_id))
            assignments = await music_uow.assignments.list_published_for_group(group_id)
            genres = await music_uow.genres.get_published_by_ids([assignment.concept_id for assignment in assignments])
            memberships = await music_uow.group_memberships.list_published_by_group(group_id)

        genre_summaries = sorted(
            (GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in genres.values()),
            key=lambda item: item.name,
        )

        members: list[GroupMemberView] = []
        async with self._people_uow_factory() as people_uow:
            for membership in memberships:
                person = await people_uow.persons.get_published(membership.person_id)
                if person is None:
                    continue
                members.append(
                    GroupMemberView(
                        id=str(person.id),
                        name=person.canonical_name,
                        period=GroupPeriodView.from_period(membership.period),
                        roles_or_instruments=list(membership.roles_or_instruments),
                    ),
                )
        members.sort(key=lambda member: member.name)

        return GroupOverviewResponse(
            id=str(group.id),
            name=group.canonical_name,
            aliases=list(group.aliases),
            description=group.description,
            period=GroupPeriodView.from_period(group.period),
            primary_image=None,
            genres=genre_summaries,
            members=members,
        )
