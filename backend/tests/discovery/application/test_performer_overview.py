from uuid import uuid7

import pytest

from roots_of_rhythm.discovery.application.errors.performers import PerformerOverviewNotFound
from roots_of_rhythm.discovery.application.performer_overview import PerformerOverviewQuery
from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationContent,
    ClassificationTargetKind,
    Genre,
)
from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus as MusicEditorialStatus,
)
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
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork
from tests.people_catalog.fakes import FakePeopleCatalogUnitOfWork


@pytest.mark.asyncio
async def test_performer_overview_returns_all_optional_content_and_published_genres() -> None:
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
    jazz = _genre("Jazz", MusicEditorialStatus.PUBLISHED)
    swing = _genre("Swing", MusicEditorialStatus.PUBLISHED)
    hidden = _genre("Hidden", MusicEditorialStatus.DRAFT)
    assignments = {
        assignment.id: assignment
        for assignment in (
            _assignment(person, swing, MusicEditorialStatus.PUBLISHED),
            _assignment(person, jazz, MusicEditorialStatus.PUBLISHED),
            _assignment(person, hidden, MusicEditorialStatus.PUBLISHED),
            _assignment(person, jazz, MusicEditorialStatus.DRAFT),
        )
    }
    query = PerformerOverviewQuery(
        lambda: FakePeopleCatalogUnitOfWork({person.id: person}),
        lambda: FakeMusicCatalogUnitOfWork(
            {genre.id: genre for genre in (jazz, swing, hidden)},
            assignments,
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
@pytest.mark.parametrize("status", [None, PersonEditorialStatus.DRAFT, PersonEditorialStatus.ARCHIVED])
async def test_performer_overview_hides_missing_and_non_public_people(
    status: PersonEditorialStatus | None,
) -> None:
    performer_id = uuid7()
    persons = (
        {}
        if status is None
        else {
            performer_id: Person.create(
                performer_id,
                PersonContent.create("Hidden"),
                editorial_status=status,
            ),
        }
    )
    query = PerformerOverviewQuery(
        lambda: FakePeopleCatalogUnitOfWork(persons),
        lambda: FakeMusicCatalogUnitOfWork({}),
    )

    with pytest.raises(PerformerOverviewNotFound):
        await query.get(performer_id)


def _genre(name: str, status: MusicEditorialStatus) -> Genre:
    return Genre(
        id=uuid7(),
        content=ClassificationContent.create(name, definition="Published definition."),
        editorial_status=status,
    )


def _assignment(
    person: Person,
    genre: Genre,
    status: MusicEditorialStatus,
) -> ClassificationAssignment:
    return ClassificationAssignment(
        id=uuid7(),
        target_kind=ClassificationTargetKind.PERSON,
        target_id=person.id,
        concept_id=genre.id,
        explanation="Classification explanation.",
        provenance="Editorial review.",
        editorial_status=status,
    )
