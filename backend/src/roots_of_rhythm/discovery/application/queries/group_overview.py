from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto.common import (
    GenreSummary,
)
from roots_of_rhythm.discovery.application.dto.groups import (
    GroupMemberView,
    GroupOverviewResponse,
    GroupPeriodView,
)
from roots_of_rhythm.discovery.application.errors.groups import GroupOverviewNotFound

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.public.group_reader import GroupReader
    from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReader


@runtime_checkable
class GroupOverviewReader(Protocol):
    async def get(self, group_id: UUID) -> GroupOverviewResponse: ...


class GroupOverviewQuery:
    def __init__(
        self,
        groups: GroupReader,
        people: PublishedPeopleReader,
    ) -> None:
        self._groups = groups
        self._people = people

    async def get(self, group_id: UUID) -> GroupOverviewResponse:
        data = await self._groups.get_group_overview(group_id)
        group = data.group
        if group is None:
            raise GroupOverviewNotFound(str(group_id))

        genre_summaries = sorted(
            (GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in data.genres.values()),
            key=lambda item: item.name,
        )

        members: list[GroupMemberView] = []
        person_ids = tuple(membership.person_id for membership in data.memberships)
        people_data = await self._people.get_published_by_ids(person_ids)
        persons = {person.id: person for person in people_data.persons}
        for membership in data.memberships:
            person = persons.get(membership.person_id)
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
