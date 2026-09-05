from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.errors.performers import PerformerOverviewNotFound
from roots_of_rhythm.discovery.application.queries.performer_overview import PerformerOverviewQuery
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    EditorialStatus,
    Genre,
)
from roots_of_rhythm.music_catalog.public.performer_reader import PerformerData
from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus as PersonEditorialStatus,
)
from roots_of_rhythm.people_catalog.domain import (
    ExternalIdentity,
    Person,
    PersonContent,
    PersonDate,
    TemporalPrecision,
)
from roots_of_rhythm.people_catalog.public.published_person_reader import PublishedPeopleReadData
from tests.discovery.readers_stubs import StubPerformerReader, StubPublishedPeopleReader


@pytest.mark.asyncio
async def test_performer_overview_query_projects_person_and_published_genres() -> None:
    person = Person.create(
        uuid7(),
        PersonContent.create(
            "Louis Armstrong",
            aliases=("Satchmo",),
            biography="Trumpeter and singer.",
            birth_date=PersonDate(1901, TemporalPrecision.EXACT_YEAR),
            death_date=PersonDate(1971, TemporalPrecision.EXACT_YEAR),
            external_identities=(
                ExternalIdentity.create(
                    "MusicBrainz",
                    "artist-1",
                    url="https://musicbrainz.org/artist/artist-1",
                ),
            ),
        ),
        editorial_status=PersonEditorialStatus.PUBLISHED,
    )
    jazz = _genre("Jazz", EditorialStatus.PUBLISHED)
    swing = _genre("Swing", EditorialStatus.PUBLISHED)
    assignments = {
        assignment.id: assignment
        for assignment in (
            _assignment(person, swing, EditorialStatus.PUBLISHED),
            _assignment(person, jazz, EditorialStatus.PUBLISHED),
        )
    }
    query = PerformerOverviewQuery(
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=(person,))),
        StubPerformerReader(
            PerformerData(
                assignments=tuple(assignments.values()),
                genres={jazz.id: jazz, swing.id: swing},
            )
        ),
    )

    response = await query.get(person.id)

    assert response.id == str(person.id)
    assert response.name == "Louis Armstrong"
    assert response.aliases == ["Satchmo"]
    assert response.biography == "Trumpeter and singer."
    assert response.birth_date is not None
    assert (response.birth_date.year, response.birth_date.precision) == (1901, TemporalPrecision.EXACT_YEAR)
    assert response.death_date is not None
    assert (response.death_date.year, response.death_date.precision) == (1971, TemporalPrecision.EXACT_YEAR)
    assert [(identity.provider, identity.identifier, identity.url) for identity in response.external_identities] == [
        ("MusicBrainz", "artist-1", "https://musicbrainz.org/artist/artist-1"),
    ]
    assert response.primary_image is None
    assert [(genre.id, genre.name) for genre in response.genres] == [
        (str(jazz.id), "Jazz"),
        (str(swing.id), "Swing"),
    ]


@pytest.mark.asyncio
async def test_performer_overview_query_hides_missing_person() -> None:
    query = PerformerOverviewQuery(
        StubPublishedPeopleReader(PublishedPeopleReadData(persons=())),
        StubPerformerReader(PerformerData(assignments=(), genres={})),
    )

    with pytest.raises(PerformerOverviewNotFound):
        await query.get(uuid7())


def _genre(name: str, status: EditorialStatus) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


def _assignment(person: Person, genre: Genre, status: EditorialStatus) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.PERSON,
        target_id=person.id,
        concept_id=genre.id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=status,
    )
