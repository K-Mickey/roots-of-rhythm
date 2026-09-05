from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import (
    FakeClassificationAssignmentRepository,
    FakeGenreRepository,
    FakeGroupMembershipRepository,
    FakeGroupRepository,
)
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.music_catalog.application.read_services.groups import GroupReadService
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


def _genre(name: str) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _group() -> Group:
    return Group.create(
        uuid7(),
        GroupContent.create("Count Basie Orchestra"),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _assignment(group_id: UUID, genre: Genre) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.GROUP,
        target_id=group_id,
        concept_id=genre.id,
        explanation="Explanation.",
        provenance="Editorial review.",
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _membership(group_id: UUID, person_id: UUID) -> GroupMembership:
    return GroupMembership.create(
        uuid7(),
        person_id,
        group_id,
        GroupMembershipContent.create(
            period=ExistencePeriod.create(
                start=TemporalBound(1935, TemporalPrecision.EXACT_YEAR),
                end=TemporalBound(1950, TemporalPrecision.EXACT_YEAR),
            ),
            roles_or_instruments=("piano",),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _service(
    group: Group,
    groups: dict[UUID, Group],
    genres_dict: dict[UUID, Genre],
    assignments: dict[UUID, ClassificationAssignment],
    memberships: dict[UUID, GroupMembership],
) -> GroupReadService:
    scope = fake_transaction_scope()
    return GroupReadService(
        scope,
        lambda _t: FakeGroupRepository(groups),
        lambda _t: FakeClassificationAssignmentRepository(assignments),
        lambda _t: FakeGroupMembershipRepository(memberships),
        lambda _t: FakeGenreRepository(genres_dict),
    )


@pytest.mark.asyncio
async def test_group_read_service_lists_published_in_order() -> None:
    hidden = Group.create(
        uuid7(),
        GroupContent.create("Hidden Band"),
        editorial_status=EditorialStatus.DRAFT,
    )
    basie = _group()
    other = Group.create(
        uuid7(),
        GroupContent.create("Zeta"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    service = _service(basie, {basie.id: basie, hidden.id: hidden, other.id: other}, {}, {}, {})

    result = await service.list_published()

    assert [item.canonical_name for item in result] == ["Count Basie Orchestra", "Zeta"]


@pytest.mark.asyncio
async def test_group_read_service_get_published_by_ids_filters() -> None:
    basie = _group()
    hidden = Group.create(
        uuid7(),
        GroupContent.create("Hidden"),
        editorial_status=EditorialStatus.DRAFT,
    )
    service = _service(basie, {basie.id: basie, hidden.id: hidden}, {}, {}, {})

    assert await service.get_published_by_ids({basie.id, hidden.id}) == {basie.id: basie}
    assert await service.get_published_by_ids(set()) == {}


@pytest.mark.asyncio
async def test_group_read_service_overview_assembles_assignments_genres_memberships() -> None:
    basie = _group()
    jazz = _genre("Jazz")
    swing = _genre("Swing")
    person_id = uuid7()
    assignment = _assignment(basie.id, jazz)
    membership = _membership(basie.id, person_id)
    service = _service(
        basie,
        {basie.id: basie},
        {jazz.id: jazz, swing.id: swing},
        {assignment.id: assignment},
        {membership.id: membership},
    )

    result = await service.get_group_overview(basie.id)

    assert result.group is basie
    assert [item.concept_id for item in result.assignments] == [jazz.id]
    assert set(result.genres.keys()) == {jazz.id}
    assert [item.person_id for item in result.memberships] == [person_id]


@pytest.mark.asyncio
async def test_group_read_service_overview_hides_missing_group() -> None:
    service = _service(_group(), {}, {}, {}, {})

    result = await service.get_group_overview(uuid7())

    assert result.group is None
    assert result.assignments == ()
    assert result.genres == {}
    assert result.memberships == ()
