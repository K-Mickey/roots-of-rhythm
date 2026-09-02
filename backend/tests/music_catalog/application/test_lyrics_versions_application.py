from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.historical_knowledge.domain import SourceAccessPolicy
from roots_of_rhythm.music_catalog.application import (
    RIGHTS_RESTRICTED_REASON,
    LyricsVersionEndpointNotPublished,
    LyricsVersionRelationService,
    LyricsVersionService,
    project_lyrics_version_body,
)
from roots_of_rhythm.music_catalog.domain import (
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionContent,
    LyricsVersionRelation,
    LyricsVersionRelationContent,
    LyricsVersionRelationType,
)

if TYPE_CHECKING:
    from uuid import UUID


def _version(
    work_id: UUID | None = None,
    language: str = "RU",
    usage_kind: LyricsUsageKind = LyricsUsageKind.READING_TRANSLATION,
    creation_method: LyricsCreationMethod = LyricsCreationMethod.ORIGINAL,
    body: str | None = None,
) -> LyricsVersion:
    return LyricsVersion.create(
        uuid7(),
        work_id or uuid7(),
        uuid7(),
        LyricsVersionContent.create(
            language_tag=language,
            usage_kind=usage_kind,
            creation_method=creation_method,
            body=body,
        ),
    )


@pytest.mark.asyncio
async def test_lyrics_version_relation_publish_requires_published_endpoints() -> None:
    versions: dict[UUID, LyricsVersion] = {}
    relations: dict[UUID, LyricsVersionRelation] = {}
    version_service = LyricsVersionService(lambda: FakeMusicCatalogUnitOfWork({}, lyrics_versions=versions))
    relation_service = LyricsVersionRelationService(
        lambda: FakeMusicCatalogUnitOfWork({}, lyrics_versions=versions, lyrics_version_relations=relations)
    )
    source_version_id = uuid7()
    source = LyricsVersionContent.create(
        language_tag="en",
        usage_kind=LyricsUsageKind.PERFORMABLE,
        creation_method=LyricsCreationMethod.ORIGINAL,
        body="Original text",
    )
    target = LyricsVersionContent.create(
        language_tag="ru",
        usage_kind=LyricsUsageKind.READING_TRANSLATION,
        creation_method=LyricsCreationMethod.HUMAN_TRANSLATION,
        body="Translated text",
    )
    source_version = await version_service.create(uuid7(), source_version_id, source)
    target_version = await version_service.create(uuid7(), source_version_id, target)
    await version_service.publish(target_version.id)
    relation = await relation_service.create(
        source_version.id,
        target_version.id,
        LyricsVersionRelationType.TRANSLATION_OF,
        LyricsVersionRelationContent.create(
            relation_type=LyricsVersionRelationType.TRANSLATION_OF,
            provenance="Editorial note.",
        ),
    )

    with pytest.raises(LyricsVersionEndpointNotPublished, match=str(source_version.id)):
        await relation_service.publish(relation.id)

    await version_service.publish(source_version.id)
    published = await relation_service.publish(relation.id)
    assert published.is_published


def test_project_lyrics_version_body_withholds_by_default() -> None:
    version = _version()
    disclosure = project_lyrics_version_body(version, SourceAccessPolicy.WITHHOLD_PUBLIC_BODY)
    assert disclosure.body is None
    assert disclosure.body_unavailable_reason == RIGHTS_RESTRICTED_REASON


def test_project_lyrics_version_body_allows_when_policy_permits() -> None:
    version = _version(body="Public lyrics")
    disclosure = project_lyrics_version_body(version, SourceAccessPolicy.ALLOW_PUBLIC_BODY)
    assert disclosure.body == "Public lyrics"
    assert disclosure.body_unavailable_reason is None
