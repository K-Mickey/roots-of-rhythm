from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionContent,
    LyricsVersionInvalidCombinationError,
    LyricsVersionPublicationError,
    LyricsVersionRelation,
    LyricsVersionRelationContent,
    LyricsVersionRelationSelfReferenceError,
    LyricsVersionRelationType,
    MusicCatalogDomainError,
)
from roots_of_rhythm.music_catalog.domain.value_objects import canonicalize_language_tag


def test_canonicalize_language_tag_accepts_short_codes() -> None:
    assert canonicalize_language_tag("en") == "en"
    assert canonicalize_language_tag("EN-gb") == "en-GB"
    assert canonicalize_language_tag("ru") == "ru"


def test_canonicalize_language_tag_rejects_invalid_tag() -> None:
    with pytest.raises(MusicCatalogDomainError, match="language tag"):
        canonicalize_language_tag("not-a-language")


def test_lyrics_version_allows_multiple_languages_and_labels() -> None:
    work_id = uuid7()
    source_version_id = uuid7()
    english = LyricsVersion.create(
        uuid7(),
        work_id,
        source_version_id,
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
            label="Original",
            body="Hello",
        ),
    )
    russian = LyricsVersion.create(
        uuid7(),
        work_id,
        source_version_id,
        LyricsVersionContent.create(
            language_tag="ru",
            usage_kind=LyricsUsageKind.READING_TRANSLATION,
            creation_method=LyricsCreationMethod.HUMAN_TRANSLATION,
            label="Reading",
            body="Привет",
        ),
    )

    assert english.language_tag == "en"
    assert russian.language_tag == "ru"
    assert english.label == "Original"
    assert russian.label == "Reading"


def test_lyrics_version_rejects_machine_translation_as_performable() -> None:
    with pytest.raises(LyricsVersionInvalidCombinationError):
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.MACHINE_TRANSLATION,
        )


def test_lyrics_version_machine_publish_requires_review() -> None:
    version = LyricsVersion.create(
        uuid7(),
        uuid7(),
        uuid7(),
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.READING_TRANSLATION,
            creation_method=LyricsCreationMethod.MACHINE_TRANSLATION,
            body="Machine text",
        ),
    )
    with pytest.raises(LyricsVersionPublicationError, match="editorial_status"):
        version.publish()

    reviewed = version.submit_for_review()
    published = reviewed.publish()
    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert published.publish().editorial_status is EditorialStatus.PUBLISHED


def test_lyrics_version_relation_rejects_self_reference() -> None:
    version_id = uuid7()
    with pytest.raises(LyricsVersionRelationSelfReferenceError):
        LyricsVersionRelation.create(
            uuid7(),
            version_id,
            version_id,
            LyricsVersionRelationType.TRANSLATION_OF,
        )


def test_lyrics_version_relation_publish_requires_provenance() -> None:
    relation = LyricsVersionRelation.create(
        uuid7(),
        uuid7(),
        uuid7(),
        LyricsVersionRelationType.ADAPTATION_OF,
    )
    with pytest.raises(MusicCatalogDomainError, match="provenance"):
        relation.publish()

    published = LyricsVersionRelation.create(
        uuid7(),
        uuid7(),
        uuid7(),
        LyricsVersionRelationType.ADAPTATION_OF,
        LyricsVersionRelationContent.create(
            relation_type=LyricsVersionRelationType.ADAPTATION_OF,
            provenance="Editorial note.",
        ),
    ).publish()
    assert published.editorial_status is EditorialStatus.PUBLISHED
