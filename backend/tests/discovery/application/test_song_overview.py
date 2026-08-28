from uuid import UUID, uuid7

import pytest

from roots_of_rhythm.discovery.application.errors import SongOverviewNotFound
from roots_of_rhythm.discovery.application.song_overview import SongOverviewQuery
from roots_of_rhythm.music_catalog.application.lyrics_body_projection import LyricsBodyDisclosure
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    ExistencePeriod,
    Genre,
    LyricsVersion,
    MusicalWork,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
    WorkCredit,
    WorkCreditContent,
    WorkCreditRole,
    WorkRelation,
    WorkRelationContent,
    WorkRelationType,
)
from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus as PersonEditorialStatus,
)
from roots_of_rhythm.people_catalog.domain import Person, PersonContent
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork


class StubLyricsProjection:
    async def disclose_bodies_for_versions(
        self,
        versions: tuple[LyricsVersion, ...],
    ) -> list[LyricsBodyDisclosure]:
        return [LyricsBodyDisclosure(body=version.body, body_unavailable_reason=None) for version in versions]


@pytest.mark.asyncio
async def test_song_overview_returns_public_fields_credits_classifications_and_related_works() -> None:
    work_id = uuid7()
    related_work_id = uuid7()
    merle_travis_id = uuid7()
    work = MusicalWork.create(
        work_id,
        WorkContent.create(
            "Sixteen Tons",
            aliases=("16 Tons",),
            description="A coal-mining song.",
            period=ExistencePeriod.create(
                start=TemporalBound(1946, TemporalPrecision.EXACT_YEAR),
                end=TemporalBound(1955, TemporalPrecision.CIRCA_YEAR),
            ),
            provenance="Editorial review.",
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    related_work = MusicalWork.create(
        related_work_id,
        WorkContent.create("Related Song", provenance="Editorial review."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    merle_travis = Person.create(
        merle_travis_id,
        PersonContent.create("Merle Travis"),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )
    hidden_person = Person.create(
        uuid7(),
        PersonContent.create("Hidden Author"),
        editorial_status=PersonEditorialStatus.DRAFT,
    )
    jazz = _genre("Jazz", EditorialStatus.PUBLISHED)
    swing = _genre("Swing", EditorialStatus.PUBLISHED)
    hidden_genre = _genre("Hidden", EditorialStatus.DRAFT)
    composer_credit = WorkCredit.create(
        uuid7(),
        work_id,
        merle_travis_id,
        WorkCreditRole.COMPOSER,
        editorial_status=EditorialStatus.PUBLISHED,
    )
    hidden_credit = WorkCredit.create(
        uuid7(),
        work_id,
        hidden_person.id,
        WorkCreditRole.LYRICIST,
        WorkCreditContent.create(role=WorkCreditRole.LYRICIST),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    draft_credit = WorkCredit.create(
        uuid7(),
        work_id,
        merle_travis_id,
        WorkCreditRole.LYRICIST,
        editorial_status=EditorialStatus.DRAFT,
    )
    relation = WorkRelation.create(
        uuid7(),
        work_id,
        related_work_id,
        WorkRelationType.ADAPTATION_OF,
        WorkRelationContent.create(
            relation_type=WorkRelationType.ADAPTATION_OF,
            provenance="Editorial review.",
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    assignments = {
        assignment.id: assignment
        for assignment in (
            _assignment(work_id, swing, EditorialStatus.PUBLISHED),
            _assignment(work_id, jazz, EditorialStatus.PUBLISHED),
            _assignment(work_id, hidden_genre, EditorialStatus.PUBLISHED),
            _assignment(work_id, jazz, EditorialStatus.DRAFT),
        )
    }
    query = SongOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {genre.id: genre for genre in (jazz, swing, hidden_genre)},
            assignments,
            works={work_id: work, related_work_id: related_work},
            work_credits={
                composer_credit.id: composer_credit,
                hidden_credit.id: hidden_credit,
                draft_credit.id: draft_credit,
            },
            work_relations={relation.id: relation},
        ),
        lambda: FakePeopleCatalogUnitOfWork(
            {merle_travis_id: merle_travis, hidden_person.id: hidden_person},
        ),
        StubLyricsProjection(),  # type: ignore[arg-type]
    )

    response = await query.get(work_id)

    assert response.id == str(work_id)
    assert response.name == "Sixteen Tons"
    assert response.aliases == ["16 Tons"]
    assert response.description == "A coal-mining song."
    assert response.period.start is not None
    assert (response.period.start.year, response.period.start.precision) == (1946, TemporalPrecision.EXACT_YEAR)
    assert response.period.end is not None
    assert (response.period.end.year, response.period.end.precision) == (1955, TemporalPrecision.CIRCA_YEAR)
    assert response.external_identities == []
    assert [(credit.person.id, credit.person.name, credit.role.value) for credit in response.credits] == [
        (str(merle_travis_id), "Merle Travis", "composer"),
    ]
    assert [(genre.id, genre.name) for genre in response.classifications] == [
        (str(jazz.id), "Jazz"),
        (str(swing.id), "Swing"),
    ]
    assert [(item.relation_type.value, item.work.id, item.work.name) for item in response.related_works] == [
        ("adaptation_of", str(related_work_id), "Related Song"),
    ]
    assert response.lyrics_versions == []


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, EditorialStatus.DRAFT, EditorialStatus.ARCHIVED])
async def test_song_overview_hides_missing_and_non_public_works(status: EditorialStatus | None) -> None:
    work_id = uuid7()
    works = (
        {}
        if status is None
        else {
            work_id: MusicalWork.create(
                work_id,
                WorkContent.create("Hidden Song", provenance="Editorial review."),
                editorial_status=status,
            ),
        }
    )
    query = SongOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork({}, works=works),
        lambda: FakePeopleCatalogUnitOfWork({}),
        StubLyricsProjection(),  # type: ignore[arg-type]
    )

    with pytest.raises(SongOverviewNotFound):
        await query.get(work_id)


@pytest.mark.asyncio
async def test_song_overview_related_works_include_only_outbound_source_relations() -> None:
    song_id = uuid7()
    original_id = uuid7()
    derivative_id = uuid7()
    song = MusicalWork.create(
        song_id,
        WorkContent.create("Current Song", provenance="Editorial review."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    original = MusicalWork.create(
        original_id,
        WorkContent.create("Original Song", provenance="Editorial review."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    derivative = MusicalWork.create(
        derivative_id,
        WorkContent.create("Derivative Song", provenance="Editorial review."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    outbound = WorkRelation.create(
        uuid7(),
        song_id,
        original_id,
        WorkRelationType.TRANSLATION_OF,
        WorkRelationContent.create(
            relation_type=WorkRelationType.TRANSLATION_OF,
            provenance="Editorial review.",
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    inbound = WorkRelation.create(
        uuid7(),
        derivative_id,
        song_id,
        WorkRelationType.ADAPTATION_OF,
        WorkRelationContent.create(
            relation_type=WorkRelationType.ADAPTATION_OF,
            provenance="Editorial review.",
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    query = SongOverviewQuery(
        lambda: FakeMusicCatalogUnitOfWork(
            {},
            works={song_id: song, original_id: original, derivative_id: derivative},
            work_relations={outbound.id: outbound, inbound.id: inbound},
        ),
        lambda: FakePeopleCatalogUnitOfWork({}),
        StubLyricsProjection(),  # type: ignore[arg-type]
    )

    response = await query.get(song_id)

    assert [(item.relation_type.value, item.work.id, item.work.name) for item in response.related_works] == [
        ("translation_of", str(original_id), "Original Song"),
    ]


def _genre(name: str, status: EditorialStatus) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


def _assignment(work_id: UUID, genre: Genre, status: EditorialStatus) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.MUSICAL_WORK,
        target_id=work_id,
        concept_id=genre.id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=status,
    )
