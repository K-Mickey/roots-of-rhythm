from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

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


def _assignment(person_id: UUID, genre_id: UUID) -> ClassificationAssignment:
    return ClassificationAssignment.create_for_person(
        uuid7(),
        person_id,
        genre_id,
        explanation="A Jazz performer.",
        provenance="Editorial review.",
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
    service = ClassificationAssignmentService(
        lambda: FakeMusicCatalogUnitOfWork({genre.id: genre}, assignments),
        lambda candidate_id: _published(candidate_id == person_id),
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
    service = ClassificationAssignmentService(
        lambda: FakeMusicCatalogUnitOfWork({genre.id: genre}, {assignment.id: assignment}),
        lambda _: _published(False),
    )

    with pytest.raises(ClassificationAssignmentPersonNotPublished):
        await service.publish(assignment.id)


@pytest.mark.asyncio
async def test_assignment_service_rejects_unpublished_genre_endpoint() -> None:
    assignment = _assignment(uuid7(), uuid7())
    service = ClassificationAssignmentService(
        lambda: FakeMusicCatalogUnitOfWork({}, {assignment.id: assignment}),
        lambda _: _published(True),
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
    service = ClassificationAssignmentService(
        lambda: FakeMusicCatalogUnitOfWork({genre.id: genre}, assignments),
        lambda candidate_id: _published(candidate_id == person_id),
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
    service = ClassificationAssignmentService(
        lambda: FakeMusicCatalogUnitOfWork({}),
        lambda _: _published(True),
    )

    with pytest.raises(ClassificationAssignmentNotFound):
        await service.replace_content(
            uuid7(),
            explanation="A Jazz performer.",
            claim_id=None,
            provenance="Editorial review.",
            evidence_status=EvidenceStatus.UNVERIFIED,
        )


async def _published(value: bool) -> bool:
    return value
