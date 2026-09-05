from uuid import UUID, uuid7

import pytest
from tests.music_catalog.fakes import FakeClassificationAssignmentRepository, FakeGenreRepository
from tests.support.scopes import fake_transaction_scope

from roots_of_rhythm.music_catalog.application.read_services.performers import PerformerReadService
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    Genre,
)


def _genre(name: str, status: EditorialStatus = EditorialStatus.PUBLISHED) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


def _assignment(person_id: UUID, genre: Genre) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.PERSON,
        target_id=person_id,
        concept_id=genre.id,
        explanation="Explanation.",
        provenance="Editorial review.",
        editorial_status=EditorialStatus.PUBLISHED,
    )


@pytest.mark.asyncio
async def test_performer_read_service_returns_assignments_and_genres() -> None:
    person_id = uuid7()
    jazz = _genre("Jazz")
    swing = _genre("Swing")
    hidden = _genre("Hidden", EditorialStatus.DRAFT)
    a1 = _assignment(person_id, jazz)
    a2 = _assignment(person_id, swing)
    a3 = _assignment(person_id, hidden)
    service = PerformerReadService(
        fake_transaction_scope(),
        lambda _t: FakeClassificationAssignmentRepository({a1.id: a1, a2.id: a2, a3.id: a3}),
        lambda _t: FakeGenreRepository({jazz.id: jazz, swing.id: swing, hidden.id: hidden}),
    )

    result = await service.get_performer_data(person_id)

    assert {item.id for item in result.assignments} == {a1.id, a2.id, a3.id}
    assert set(result.genres.keys()) == {jazz.id, swing.id}
