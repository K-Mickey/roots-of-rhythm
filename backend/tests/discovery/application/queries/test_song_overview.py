from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.errors.songs import SongOverviewNotFound
from roots_of_rhythm.discovery.application.queries.song_overview import SongOverviewQuery
from roots_of_rhythm.music_catalog.domain import (
    ClassificationContent,
    EditorialStatus,
    ExistencePeriod,
    Genre,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionRelation,
    LyricsVersionRelationType,
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
from roots_of_rhythm.music_catalog.public.song_overview_reader import SongMusicReadData
from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus as PersonEditorialStatus,
)
from roots_of_rhythm.people_catalog.domain import Person, PersonContent
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.readers_stubs import (
    StubPublishedPeopleReader,
    StubSongHistoricalKnowledgeReader,
    StubSongMusicReader,
)


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
    query = SongOverviewQuery(
        StubSongMusicReader(
            SongMusicReadData(
                work,
                work_credits=(composer_credit, hidden_credit),
                genres=(jazz, swing),
                work_relations=(relation,),
                related_works=(related_work,),
            )
        ),
        StubPublishedPeopleReader(PublishedPeopleReadData((merle_travis,))),
        StubSongHistoricalKnowledgeReader(),
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
    assert response.recording_genres == []
    assert response.recordings == []


@pytest.mark.asyncio
async def test_song_overview_shows_each_relation_once_for_each_published_endpoint() -> None:
    work_id = uuid7()
    first = LyricsVersion(
        uuid7(),
        work_id,
        uuid7(),
        "en",
        LyricsUsageKind.PERFORMABLE,
        LyricsCreationMethod.ORIGINAL,
        editorial_status=EditorialStatus.PUBLISHED,
    )
    second = LyricsVersion(
        uuid7(),
        work_id,
        uuid7(),
        "ru",
        LyricsUsageKind.READING_TRANSLATION,
        LyricsCreationMethod.HUMAN_TRANSLATION,
        editorial_status=EditorialStatus.PUBLISHED,
    )
    relation = LyricsVersionRelation(
        uuid7(),
        first.id,
        second.id,
        LyricsVersionRelationType.TRANSLATION_OF,
        editorial_status=EditorialStatus.PUBLISHED,
    )
    work = MusicalWork.create(
        work_id,
        WorkContent.create("Song", provenance="Editorial review."),
        editorial_status=EditorialStatus.PUBLISHED,
    )
    response = await SongOverviewQuery(
        StubSongMusicReader(
            SongMusicReadData(work, lyrics_versions=(first, second), lyrics_relations=(relation,)),
        ),
        StubPublishedPeopleReader(PublishedPeopleReadData(())),
        StubSongHistoricalKnowledgeReader(),
    ).get(work_id)

    assert [len(item.relations) for item in response.lyrics_versions] == [1, 1]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [None, EditorialStatus.DRAFT, EditorialStatus.ARCHIVED])
async def test_song_overview_hides_missing_and_non_public_works(status: EditorialStatus | None) -> None:
    work_id = uuid7()
    query = SongOverviewQuery(
        StubSongMusicReader(SongMusicReadData(None)),
        StubPublishedPeopleReader(PublishedPeopleReadData(())),
        StubSongHistoricalKnowledgeReader(),
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
        StubSongMusicReader(
            SongMusicReadData(
                song,
                work_relations=(outbound, inbound),
                related_works=(original,),
            )
        ),
        StubPublishedPeopleReader(PublishedPeopleReadData(())),
        StubSongHistoricalKnowledgeReader(),
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
