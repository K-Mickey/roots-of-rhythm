from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    ClassificationConcept,
    ClassificationContent,
    ClassificationKind,
    EditorialStatus,
    Genre,
    GenrePublicationError,
    HistoricalPeriod,
    MusicCatalogDomainError,
    TemporalBound,
    TemporalPrecision,
)


def test_genre_is_a_classification_concept_with_a_fixed_kind() -> None:
    genre = Genre(id=uuid7(), content=ClassificationContent.create(" Swing "))

    assert isinstance(genre, ClassificationConcept)
    assert genre.kind is ClassificationKind.GENRE
    assert genre.content.canonical_name == "Swing"
    assert genre.content.definition is None
    assert genre.content.aliases == ()
    assert genre.content.characteristic_features == ()


def test_publication_requires_only_definition_and_preserves_identity() -> None:
    genre = Genre(id=uuid7(), content=ClassificationContent.create("Swing"))

    with pytest.raises(GenrePublicationError) as error:
        genre.publish()

    assert error.value.missing_fields == ("definition",)

    complete = genre.replace_content(ClassificationContent.create("Swing", definition=" Big-band jazz. "))
    published = complete.publish()
    archived = published.archive()
    republished = archived.publish()

    assert published.content.definition == "Big-band jazz."
    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert archived.editorial_status is EditorialStatus.ARCHIVED
    assert republished.editorial_status is EditorialStatus.PUBLISHED
    assert {complete.id, published.id, archived.id, republished.id} == {genre.id}


def test_published_genre_cannot_drop_definition_via_replace_content() -> None:
    published = Genre(
        id=uuid7(),
        content=ClassificationContent.create("Swing", definition="A jazz genre."),
        editorial_status=EditorialStatus.PUBLISHED,
    )

    with pytest.raises(GenrePublicationError) as error:
        published.replace_content(ClassificationContent.create("Swing"))

    assert error.value.missing_fields == ("definition",)

    updated = published.replace_content(
        ClassificationContent.create("Swing", definition="Updated definition."),
    )
    assert updated.editorial_status is EditorialStatus.PUBLISHED
    assert updated.content.definition == "Updated definition."


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (ClassificationContent.create, "canonical name must not be empty"),
        (lambda _: ClassificationContent.create("Swing", aliases=("swing",)), "aliases must not duplicate"),
        (lambda _: ClassificationContent.create("Swing", aliases=("Big Band", "big band")), "aliases must not contain"),
        (lambda _: ClassificationContent.create("Swing", definition=" "), "definition must not be empty"),
        (
            lambda _: ClassificationContent.create("Swing", characteristic_features=("Riffs", " riffs ")),
            "characteristic features must not contain",
        ),
        (lambda _: ClassificationContent.create("x" * 65), "canonical name must be at most 64"),
        (lambda _: ClassificationContent.create("Swing", definition="x" * 1025), "definition must be at most 1024"),
    ],
)
def test_content_rejects_empty_or_duplicate_values(content: object, message: str) -> None:
    factory = content if callable(content) else ClassificationContent.create
    with pytest.raises(MusicCatalogDomainError, match=message):
        factory(" ")


def test_period_rejects_reversed_bounds() -> None:
    with pytest.raises(MusicCatalogDomainError, match="start must not be later"):
        HistoricalPeriod.create(
            label="1940s–1930s",
            start=TemporalBound(1940, TemporalPrecision.DECADE),
            end=TemporalBound(1930, TemporalPrecision.DECADE),
        )


def test_mapping_rehydrates_without_renormalizing() -> None:
    content = ClassificationContent(
        canonical_name="  Swing  ",
        aliases=("  Big Band  ",),
        definition="  padded  ",
    )
    assert content.canonical_name == "  Swing  "
    assert content.aliases == ("  Big Band  ",)
    assert content.definition == "  padded  "
