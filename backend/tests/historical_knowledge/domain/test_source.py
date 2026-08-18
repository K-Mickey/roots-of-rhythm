from uuid import uuid7

import pytest

from roots_of_rhythm.historical_knowledge.domain import Source
from roots_of_rhythm.historical_knowledge.domain.errors import HistoricalKnowledgeDomainError
from roots_of_rhythm.historical_knowledge.domain.value_objects import SHORT_TEXT_MAX_LENGTH, URL_MAX_LENGTH


def test_source_create_accepts_bibliographic_fields() -> None:
    source_id = uuid7()
    source = Source.create(
        "Jazz",
        author=None,
        responsible_organization="Smithsonian Music",
        publication=None,
        publication_date=None,
        external_url="https://music.si.edu/story/jazz",
        source_id=source_id,
    )

    assert source.id == source_id
    assert source.title == "Jazz"
    assert source.author is None
    assert source.responsible_organization == "Smithsonian Music"
    assert source.publication is None
    assert source.publication_date is None
    assert source.external_url == "https://music.si.edu/story/jazz"


def test_source_create_rejects_empty_title() -> None:
    with pytest.raises(HistoricalKnowledgeDomainError, match="source title"):
        Source.create("   ")


def test_source_create_rejects_overlong_url() -> None:
    with pytest.raises(HistoricalKnowledgeDomainError, match="external url"):
        Source.create("Jazz", external_url="https://example.com/" + ("a" * URL_MAX_LENGTH))


def test_source_create_rejects_overlong_optional_text() -> None:
    with pytest.raises(HistoricalKnowledgeDomainError, match="author"):
        Source.create("Jazz", author="x" * (SHORT_TEXT_MAX_LENGTH + 1))
