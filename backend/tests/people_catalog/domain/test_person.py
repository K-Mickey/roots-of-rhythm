from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.people_catalog.domain import (
    EditorialStatus,
    ExternalIdentity,
    PeopleCatalogDomainError,
    Person,
    PersonContent,
    PersonDate,
    TemporalPrecision,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def test_person_content_normalizes_all_optional_values() -> None:
    content = PersonContent.create(
        " Louis Armstrong ",
        aliases=(" Satchmo ", "Pops"),
        biography=" Trumpeter and singer. ",
        birth_date=PersonDate(1901, TemporalPrecision.EXACT_YEAR),
        death_date=PersonDate(1971, TemporalPrecision.EXACT_YEAR),
        external_identities=(
            ExternalIdentity.create(
                " MusicBrainz ",
                " artist-1 ",
                url=" https://musicbrainz.org/artist/artist-1 ",
            ),
        ),
    )

    assert content.canonical_name == "Louis Armstrong"
    assert content.aliases == ("Satchmo", "Pops")
    assert content.biography == "Trumpeter and singer."
    assert content.birth_date == PersonDate(1901, TemporalPrecision.EXACT_YEAR)
    assert content.death_date == PersonDate(1971, TemporalPrecision.EXACT_YEAR)
    assert content.external_identities == (
        ExternalIdentity(
            provider="MusicBrainz",
            identifier="artist-1",
            url="https://musicbrainz.org/artist/artist-1",
        ),
    )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (lambda: PersonContent.create("Louis Armstrong", aliases=("louis armstrong",)), "canonical name"),
        (lambda: PersonContent.create("Louis", aliases=("Satchmo", "satchmo")), "aliases must not contain"),
        (
            lambda: PersonContent.create(
                "Louis",
                external_identities=(
                    ExternalIdentity.create("MusicBrainz", "one"),
                    ExternalIdentity.create("musicbrainz", "ONE"),
                ),
            ),
            "external identities must not contain",
        ),
        (
            lambda: PersonContent.create(
                "Louis",
                birth_date=PersonDate(1971, TemporalPrecision.EXACT_YEAR),
                death_date=PersonDate(1901, TemporalPrecision.EXACT_YEAR),
            ),
            "birth year must not be later",
        ),
        (lambda: ExternalIdentity.create("Discogs", "one", url="ftp://example.com/one"), "http or https"),
    ],
)
def test_person_value_objects_reject_invalid_content(content: Callable[[], object], message: str) -> None:
    with pytest.raises(PeopleCatalogDomainError, match=message):
        content()


def test_person_publication_requires_only_canonical_name_and_preserves_content() -> None:
    content = PersonContent.create("Louis Armstrong")
    person = Person.create(uuid7(), content)

    published = person.publish()
    archived = published.archive()

    assert published.canonical_name == content.canonical_name
    assert published.aliases == content.aliases
    assert published.biography == content.biography
    assert published.birth_date == content.birth_date
    assert published.death_date == content.death_date
    assert published.external_identities == content.external_identities
    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert archived.editorial_status is EditorialStatus.ARCHIVED
    assert published.id == archived.id == person.id
