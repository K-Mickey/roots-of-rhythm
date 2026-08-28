from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    ExistencePeriod,
    ExternalIdentity,
    MusicalWork,
    MusicalWorkPublicationError,
    MusicCatalogDomainError,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def test_work_content_normalizes_optional_values() -> None:
    period = ExistencePeriod.create(
        start=TemporalBound(1937, TemporalPrecision.EXACT_YEAR),
        end=TemporalBound(1945, TemporalPrecision.CIRCA_YEAR),
    )
    content = WorkContent.create(
        " One O'Clock Jump ",
        aliases=(" Jump Blues Standard ",),
        description=" A swing standard. ",
        period=period,
        external_identities=(
            ExternalIdentity.create("MusicBrainz", "work-123", url="https://musicbrainz.org/work/123"),
        ),
        provenance=" Editorial seed note. ",
    )

    assert content.canonical_title == "One O'Clock Jump"
    assert content.aliases == ("Jump Blues Standard",)
    assert content.description == "A swing standard."
    assert content.period == period
    assert content.provenance == "Editorial seed note."
    assert content.external_identities[0].provider == "MusicBrainz"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (lambda: WorkContent.create("Jump", aliases=("jump",)), "canonical title"),
        (lambda: WorkContent.create("Jump", aliases=("Blues", "blues")), "aliases must not contain"),
        (
            lambda: WorkContent.create(
                "Jump",
                external_identities=(
                    ExternalIdentity.create("MusicBrainz", "same"),
                    ExternalIdentity.create("musicbrainz", "same"),
                ),
            ),
            "external identities must not contain duplicates",
        ),
        (
            lambda: ExternalIdentity.create("MusicBrainz", "work-1", url="ftp://example.com/work"),
            "external identity URL must use http or https",
        ),
    ],
)
def test_work_value_objects_reject_invalid_content(content: Callable[[], object], message: str) -> None:
    with pytest.raises(MusicCatalogDomainError, match=message):
        content()


def test_musical_work_publish_requires_title_and_provenance() -> None:
    work = MusicalWork.create(uuid7(), WorkContent.create("Ornithology"))
    with pytest.raises(MusicalWorkPublicationError) as error:
        work.publish()

    assert error.value.missing_fields == ("provenance",)


def test_musical_work_publish_with_title_and_provenance_only() -> None:
    work = MusicalWork.create(
        uuid7(),
        WorkContent.create("West End Blues", provenance="Editorial seed."),
    )
    published = work.publish()

    assert published.editorial_status is EditorialStatus.PUBLISHED
    assert published.canonical_title == "West End Blues"
    assert published.aliases == ()
    assert published.description is None
    assert published.period is None
    assert published.external_identities == ()


def test_musical_work_allows_duplicate_titles() -> None:
    first = MusicalWork.create(uuid7(), WorkContent.create("Sixteen Tons", provenance="Seed A."))
    second = MusicalWork.create(uuid7(), WorkContent.create("Sixteen Tons", provenance="Seed B."))

    assert first.id != second.id
    assert first.canonical_title == second.canonical_title
