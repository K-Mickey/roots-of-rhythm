from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import FakeClassificationAssignmentRepository, FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork

from roots_of_rhythm.music_catalog.application import (
    ClassificationAssignmentConflict,
    ClassificationAssignmentGenreNotPublished,
    ClassificationAssignmentGroupNotPublished,
    ClassificationAssignmentNotFound,
    ClassificationAssignmentPersonNotPublished,
    ClassificationAssignmentService,
    ClassificationAssignmentTargetUnsupported,
    PublishClassificationAssignment,
    UniqueConstraintViolation,
)
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    EvidenceStatus,
    Genre,
    Group,
    GroupContent,
)
from roots_of_rhythm.people_catalog.domain import EditorialStatus as PersonEditorialStatus
from roots_of_rhythm.people_catalog.domain import Person, PersonContent


def _assignment(person_id: UUID, genre_id: UUID) -> ClassificationAssignment:
    return ClassificationAssignment.create_for_person(
        uuid7(),
        person_id,
        genre_id,
        explanation="A Jazz performer.",
        provenance="Editorial review.",
    )


def _published_person(person_id: UUID) -> Person:
    return Person.create(
        person_id,
        PersonContent.create("Performer"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )


def _group_assignment(group_id: UUID, genre_id: UUID) -> ClassificationAssignment:
    return ClassificationAssignment.create_for_group(
        uuid7(),
        group_id,
        genre_id,
        explanation="A Jazz group.",
        provenance="Editorial review.",
    )


def _published_group(group_id: UUID) -> Group:
    return Group.create(
        group_id,
        GroupContent.create("Count Basie Orchestra"),
        editorial_status=EditorialStatus.PUBLISHED,
    )


class _ConflictingAssignmentRepository(FakeClassificationAssignmentRepository):
    async def add(self, assignment: ClassificationAssignment) -> None:
        raise UniqueConstraintViolation("assignment constraint")


def _operations(
    *,
    genres: dict[UUID, Genre],
    assignments: dict[UUID, ClassificationAssignment],
    persons: dict[UUID, Person] | None = None,
    groups: dict[UUID, Group] | None = None,
) -> tuple[ClassificationAssignmentService, PublishClassificationAssignment]:
    music = FakeMusicCatalogUnitOfWork(genres, assignments, groups=groups or {})
    people = FakePeopleCatalogUnitOfWork(persons or {})
    service = ClassificationAssignmentService(
        lambda: music,
        lambda _transaction: music.assignments,
    )
    publish = PublishClassificationAssignment(
        lambda: music,
        lambda _transaction: music.assignments,
        lambda _transaction: music.genres,
        lambda _transaction: music.groups,
        lambda _transaction: people.persons,
    )
    return service, publish


@pytest.mark.asyncio
async def test_assignment_service_publishes_only_with_published_person_and_genre() -> None:
    person_id = uuid7()
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Jazz", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _assignment(person_id, genre.id)
    assignments = {assignment.id: assignment}
    _service, publish = _operations(
        genres={genre.id: genre},
        assignments=assignments,
        persons={person_id: _published_person(person_id)},
    )

    published = await publish.execute(assignment.id)

    assert published.is_published
    assert assignments[assignment.id] == published


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_person_endpoint() -> None:
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Jazz", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _assignment(uuid7(), genre.id)
    _service, publish = _operations(genres={genre.id: genre}, assignments={assignment.id: assignment})

    with pytest.raises(ClassificationAssignmentPersonNotPublished):
        await publish.execute(assignment.id)


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_genre_endpoint() -> None:
    person_id = uuid7()
    assignment = _assignment(person_id, uuid7())
    _service, publish = _operations(
        genres={},
        assignments={assignment.id: assignment},
        persons={person_id: _published_person(person_id)},
    )

    with pytest.raises(ClassificationAssignmentGenreNotPublished):
        await publish.execute(assignment.id)


@pytest.mark.asyncio
async def test_assignment_service_replace_content_preserves_status_and_endpoints() -> None:
    person_id = uuid7()
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Jazz", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _assignment(person_id, genre.id)
    assignments = {assignment.id: assignment}
    service, publish = _operations(
        genres={genre.id: genre},
        assignments=assignments,
        persons={person_id: _published_person(person_id)},
    )
    await publish.execute(assignment.id)
    claim_id = uuid7()

    updated = await service.replace_content(
        assignment.id,
        explanation=None,
        claim_id=claim_id,
        provenance="Seed provenance.",
        evidence_status=EvidenceStatus.UNVERIFIED,
    )

    assert updated.is_published
    assert updated.target_id == person_id
    assert updated.concept_id == genre.id
    assert updated.explanation is None
    assert updated.claim_id == claim_id
    assert updated.provenance == "Seed provenance."
    assert assignments[assignment.id] == updated


@pytest.mark.asyncio
async def test_assignment_service_replace_content_reports_missing_assignment() -> None:
    service, _publish = _operations(genres={}, assignments={})

    with pytest.raises(ClassificationAssignmentNotFound):
        await service.replace_content(
            uuid7(),
            explanation="A Jazz performer.",
            claim_id=None,
            provenance="Editorial review.",
            evidence_status=EvidenceStatus.UNVERIFIED,
        )


@pytest.mark.asyncio
async def test_assignment_service_publishes_group_assignment_with_published_group_and_genre() -> None:
    group_id = uuid7()
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Jazz", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _group_assignment(group_id, genre.id)
    assignments = {assignment.id: assignment}
    _service, publish = _operations(
        genres={genre.id: genre},
        assignments=assignments,
        groups={group_id: _published_group(group_id)},
    )

    published = await publish.execute(assignment.id)

    assert published.is_group_target
    assert published.is_published
    assert assignments[assignment.id] == published


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_group_endpoint() -> None:
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Swing", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _group_assignment(uuid7(), genre.id)
    _service, publish = _operations(genres={genre.id: genre}, assignments={assignment.id: assignment})

    with pytest.raises(ClassificationAssignmentGroupNotPublished):
        await publish.execute(assignment.id)


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_genre_for_group_assignment() -> None:
    group_id = uuid7()
    assignment = _group_assignment(group_id, uuid7())
    _service, publish = _operations(
        genres={},
        assignments={assignment.id: assignment},
        groups={group_id: _published_group(group_id)},
    )

    with pytest.raises(ClassificationAssignmentGenreNotPublished):
        await publish.execute(assignment.id)


@pytest.mark.asyncio
async def test_publish_assignment_reports_missing_assignment() -> None:
    _service, publish = _operations(genres={}, assignments={})

    with pytest.raises(ClassificationAssignmentNotFound):
        await publish.execute(uuid7())


@pytest.mark.asyncio
async def test_publish_assignment_rejects_unsupported_target() -> None:
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Jazz", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.MUSICAL_WORK,
        target_id=uuid7(),
        concept_id=genre.id,
        explanation="A Jazz work.",
        provenance="Editorial review.",
    )
    _service, publish = _operations(genres={genre.id: genre}, assignments={assignment.id: assignment})

    with pytest.raises(ClassificationAssignmentTargetUnsupported):
        await publish.execute(assignment.id)


@pytest.mark.asyncio
async def test_assignment_service_translates_repository_conflict() -> None:
    transaction = FakeMusicCatalogUnitOfWork({})
    assignment_repository = _ConflictingAssignmentRepository({})
    service = ClassificationAssignmentService(lambda: transaction, lambda _transaction: assignment_repository)

    with pytest.raises(ClassificationAssignmentConflict):
        await service.create_for_person(uuid7(), uuid7())


@pytest.mark.asyncio
async def test_publish_assignment_locks_person_and_genre_but_not_group() -> None:
    person_id = uuid7()
    genre_id = uuid7()
    assignment = _assignment(person_id, genre_id)
    transaction = FakeMusicCatalogUnitOfWork({})
    assignment_repository = Mock()
    assignment_repository.get = AsyncMock(return_value=assignment)
    assignment_repository.save = AsyncMock()
    genre_repository = Mock()
    genre_repository.get_published = AsyncMock(return_value=object())
    person_repository = Mock()
    person_repository.get_published = AsyncMock(return_value=object())
    group_repository_factory = Mock()
    publish = PublishClassificationAssignment(
        lambda: transaction,
        lambda _transaction: assignment_repository,
        lambda _transaction: genre_repository,
        group_repository_factory,
        lambda _transaction: person_repository,
    )

    await publish.execute(assignment.id)

    assignment_repository.get.assert_awaited_once_with(assignment.id, for_update=True)
    genre_repository.get_published.assert_awaited_once_with(genre_id, for_update=True)
    person_repository.get_published.assert_awaited_once_with(person_id, for_update=True)
    group_repository_factory.assert_not_called()
