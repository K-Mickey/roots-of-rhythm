from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.recording_list import RecordingListQuery
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    ExistencePeriod,
    Genre,
    Group,
    GroupContent,
    MusicalWork,
    Recording,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
)
from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus as PersonEditorialStatus,
)
from roots_of_rhythm.people_catalog.domain import Person, PersonContent
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork


def _genre(name: str) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=EditorialStatus.PUBLISHED,
    )


def _assignment(recording_id: UUID, genre: Genre) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.RECORDING,
        target_id=recording_id,
        concept_id=genre.id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=EditorialStatus.PUBLISHED,
    )


@pytest.mark.asyncio
async def test_recording_list_omits_recordings_without_published_primary() -> None:
    work_id = uuid7()
    person_id = uuid7()
    group_id = uuid7()
    jazz = _genre("Jazz")
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Take Five"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    person = Person.create(
        person_id,
        PersonContent.create("Dave Brubeck"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )
    group = Group.create(
        group_id,
        GroupContent.create("Dave Brubeck Quartet"),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    visible = Recording.create(
        uuid7(),
        RecordingContent.create(
            "Take Five",
            recorded_period=ExistencePeriod.create(
                start=TemporalBound(1959, TemporalPrecision.EXACT_YEAR),
            ),
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.GROUP,
                    group_id,
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    hidden = Recording.create(
        uuid7(),
        RecordingContent.create(
            "Hidden Primary",
            recording_credits=(
                RecordingCredit.create(
                    uuid7(),
                    RecordingCreditTargetKind.PERSON,
                    person_id,
                    BillingRole.ADDITIONAL,
                ),
            ),
            work_usages=(RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.COMPLETE),),
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignment = _assignment(visible.id, jazz)
    query = RecordingListQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {jazz.id: jazz},
            {assignment.id: assignment},
            groups={group_id: group},
            works={work_id: work},
            recordings={visible.id: visible, hidden.id: hidden},
        ),
        lambda: FakePeopleCatalogUnitOfWork({person_id: person}),
    )

    response = await query.list()

    assert [item.title for item in response.items] == ["Take Five"]
    assert response.items[0].primary_credits[0].target.name == "Dave Brubeck Quartet"
    assert len(response.items[0].genres) == 1
    assert response.items[0].genres[0].name == "Jazz"
