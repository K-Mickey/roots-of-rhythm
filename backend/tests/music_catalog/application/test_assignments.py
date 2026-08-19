from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork
from tests.support.scopes import pair_scope

from roots_of_rhythm.music_catalog.application import (
    ClassificationAssignmentGenreNotPublished,
    ClassificationAssignmentNotFound,
    ClassificationAssignmentPersonNotPublished,
    ClassificationAssignmentService,
)
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    EditorialStatus,
    EvidenceStatus,
    Genre,
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


def _service(
    *,
    genres: dict[UUID, Genre],
    assignments: dict[UUID, ClassificationAssignment],
    persons: dict[UUID, Person] | None = None,
) -> ClassificationAssignmentService:
    return ClassificationAssignmentService(
        pair_scope(
            lambda: FakeMusicCatalogUnitOfWork(genres, assignments),
            lambda: FakePeopleCatalogUnitOfWork(persons or {}),
        )
    )


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
    service = _service(
        genres={genre.id: genre},
        assignments=assignments,
        persons={person_id: _published_person(person_id)},
    )

    published = await service.publish(assignment.id)

    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert assignments[assignment.id] == published


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_person_endpoint() -> None:
    genre = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Jazz", definition="A genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _assignment(uuid7(), genre.id)
    service = _service(genres={genre.id: genre}, assignments={assignment.id: assignment})

    with pytest.raises(ClassificationAssignmentPersonNotPublished):
        await service.publish(assignment.id)


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_genre_endpoint() -> None:
    person_id = uuid7()
    assignment = _assignment(person_id, uuid7())
    service = _service(
        genres={},
        assignments={assignment.id: assignment},
        persons={person_id: _published_person(person_id)},
    )

    with pytest.raises(ClassificationAssignmentGenreNotPublished):
        await service.publish(assignment.id)


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
    service = _service(
        genres={genre.id: genre},
        assignments=assignments,
        persons={person_id: _published_person(person_id)},
    )
    await service.publish(assignment.id)
    claim_id = uuid7()

    updated = await service.replace_content(
        assignment.id,
        explanation=None,
        claim_id=claim_id,
        provenance="Seed provenance.",
        evidence_status=EvidenceStatus.UNVERIFIED,
    )

    assert updated.editorial_status is EditorialStatus.PUBLISHED
    assert updated.target_id == person_id
    assert updated.concept_id == genre.id
    assert updated.explanation is None
    assert updated.claim_id == claim_id
    assert updated.provenance == "Seed provenance."
    assert assignments[assignment.id] == updated


@pytest.mark.asyncio
async def test_assignment_service_replace_content_reports_missing_assignment() -> None:
    service = _service(genres={}, assignments={})

    with pytest.raises(ClassificationAssignmentNotFound):
        await service.replace_content(
            uuid7(),
            explanation="A Jazz performer.",
            claim_id=None,
            provenance="Editorial review.",
            evidence_status=EvidenceStatus.UNVERIFIED,
        )
