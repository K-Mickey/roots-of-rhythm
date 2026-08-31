from typing import TYPE_CHECKING
from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.errors.groups import GroupOverviewNotFound
from roots_of_rhythm.discovery.application.group_overview import GroupOverviewQuery
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    ExistencePeriod,
    Genre,
    Group,
    GroupContent,
    GroupMembership,
    GroupMembershipContent,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus as PersonEditorialStatus,
)
from roots_of_rhythm.people_catalog.domain import Person, PersonContent
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork, FakePersonRepository

if TYPE_CHECKING:
    from collections.abc import Collection


class SpyPersonRepository(FakePersonRepository):
    def __init__(self, persons: dict[UUID, Person]) -> None:
        super().__init__(persons)
        self.published_by_ids_calls: list[set[UUID]] = []

    async def get_published_by_ids(
        self, person_ids: "Collection[UUID]", *, for_update: bool = False
    ) -> dict[UUID, Person]:
        self.published_by_ids_calls.append(set(person_ids))
        return await super().get_published_by_ids(person_ids, for_update=for_update)


@pytest.mark.asyncio
async def test_group_overview_returns_public_fields_genres_and_members() -> None:
    group_id = uuid7()
    count_basie_id = uuid7()
    freddie_green_id = uuid7()
    hidden_person_id = uuid7()
    group = Group.create(
        group_id,
        GroupContent.create(
            "Count Basie Orchestra",
            aliases=("Basie band",),
            description="A swing orchestra.",
            period=ExistencePeriod.create(
                start=TemporalBound(1935, TemporalPrecision.EXACT_YEAR),
                end=TemporalBound(1950, TemporalPrecision.CIRCA_YEAR),
            ),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    count_basie = Person.create(
        count_basie_id,
        PersonContent.create("Count Basie"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )
    hidden_person = Person.create(
        hidden_person_id,
        PersonContent.create("Hidden Performer"),
        editorial_status=PersonEditorialStatus.DRAFT,
    )
    freddie_green = Person.create(
        freddie_green_id,
        PersonContent.create("Freddie Green"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )
    jazz = _genre("Jazz", EditorialStatus.PUBLISHED)
    swing = _genre("Swing", EditorialStatus.PUBLISHED)
    hidden_genre = _genre("Hidden", EditorialStatus.DRAFT)
    published_membership = GroupMembership.create(
        uuid7(),
        count_basie_id,
        group_id,
        GroupMembershipContent.create(
            period=ExistencePeriod.create(
                start=TemporalBound(1935, TemporalPrecision.EXACT_YEAR),
                end=TemporalBound(1950, TemporalPrecision.CIRCA_YEAR),
            ),
            roles_or_instruments=("piano", "bandleader"),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    hidden_membership = GroupMembership.create(
        uuid7(),
        hidden_person_id,
        group_id,
        GroupMembershipContent.create(roles_or_instruments=("vocals",)),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    second_published_membership = GroupMembership.create(
        uuid7(),
        freddie_green_id,
        group_id,
        GroupMembershipContent.create(roles_or_instruments=("guitar",)),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignments = {
        assignment.id: assignment
        for assignment in (
            _assignment(group_id, swing, EditorialStatus.PUBLISHED),
            _assignment(group_id, jazz, EditorialStatus.PUBLISHED),
            _assignment(group_id, hidden_genre, EditorialStatus.PUBLISHED),
            _assignment(group_id, jazz, EditorialStatus.DRAFT),
        )
    }
    people_uow = FakePeopleCatalogUnitOfWork(
        {count_basie_id: count_basie, freddie_green_id: freddie_green, hidden_person_id: hidden_person},
    )
    people = SpyPersonRepository(
        {count_basie_id: count_basie, freddie_green_id: freddie_green, hidden_person_id: hidden_person},
    )
    people_uow.persons = people
    query = GroupOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {genre.id: genre for genre in (jazz, swing, hidden_genre)},
            assignments,
            groups={group_id: group},
            group_memberships={
                published_membership.id: published_membership,
                second_published_membership.id: second_published_membership,
                hidden_membership.id: hidden_membership,
            },
        ),
        lambda: people_uow,
    )

    response = await query.get(group_id)

    assert response.id == str(group_id)
    assert response.name == "Count Basie Orchestra"
    assert response.aliases == ["Basie band"]
    assert response.description == "A swing orchestra."
    assert response.period.start is not None
    assert (response.period.start.year, response.period.start.precision) == (1935, TemporalPrecision.EXACT_YEAR)
    assert response.period.end is not None
    assert (response.period.end.year, response.period.end.precision) == (1950, TemporalPrecision.CIRCA_YEAR)
    assert response.primary_image is None
    assert [(genre.id, genre.name) for genre in response.genres] == [
        (str(jazz.id), "Jazz"),
        (str(swing.id), "Swing"),
    ]
    assert [(member.id, member.name, member.roles_or_instruments) for member in response.members] == [
        (str(count_basie_id), "Count Basie", ["piano", "bandleader"]),
        (str(freddie_green_id), "Freddie Green", ["guitar"]),
    ]
    assert people.published_by_ids_calls == [{count_basie_id, freddie_green_id, hidden_person_id}]
    assert response.members[0].period.start is not None
    assert (response.members[0].period.start.year, response.members[0].period.start.precision) == (
        1935,
        TemporalPrecision.EXACT_YEAR,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, EditorialStatus.DRAFT, EditorialStatus.ARCHIVED])
async def test_group_overview_hides_missing_and_non_public_groups(status: EditorialStatus | None) -> None:
    group_id = uuid7()
    groups = (
        {}
        if status is None
        else {
            group_id: Group.create(
                group_id,
                GroupContent.create("Hidden Group"),
                editorial_status=status,
            ),
        }
    )
    query = GroupOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork({}, groups=groups),
        lambda: FakePeopleCatalogUnitOfWork({}),
    )

    with pytest.raises(GroupOverviewNotFound):
        await query.get(group_id)


def _genre(name: str, status: EditorialStatus) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


def _assignment(group_id: UUID, genre: Genre, status: EditorialStatus) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.GROUP,
        target_id=group_id,
        concept_id=genre.id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=status,
    )
