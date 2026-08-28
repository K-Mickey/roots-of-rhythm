from uuid import uuid7

import pytest
from tests.historical_knowledge.fakes import FakeHistoricalKnowledgeUnitOfWork, FakeSourceRepository
from tests.music_catalog.fakes import FakeMusicCatalogUnitOfWork

from roots_of_rhythm.historical_knowledge.domain import Source, SourceAccessPolicy, SourceVersion
from roots_of_rhythm.music_catalog.application.lyrics_body_projection import RIGHTS_RESTRICTED_REASON
from roots_of_rhythm.music_catalog.application.lyrics_version_projection_service import (
    LyricsVersionProjectionService,
)
from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionContent,
)


@pytest.mark.asyncio
async def test_disclose_bodies_for_versions_uses_one_hk_uow_and_preserves_order() -> None:
    sources = FakeSourceRepository()
    allowed = Source.create("Allowed corpus", access_policy=SourceAccessPolicy.ALLOW_PUBLIC_BODY)
    withheld = Source.create("Withheld corpus", access_policy=SourceAccessPolicy.WITHHOLD_PUBLIC_BODY)
    allowed_version = SourceVersion.create(allowed.id, "v1")
    withheld_version = SourceVersion.create(withheld.id, "v1")
    sources.sources = {allowed.id: allowed, withheld.id: withheld}
    sources.versions = {allowed_version.id: allowed_version, withheld_version.id: withheld_version}

    hk_entries: list[FakeHistoricalKnowledgeUnitOfWork] = []

    def hk_factory() -> FakeHistoricalKnowledgeUnitOfWork:
        uow = FakeHistoricalKnowledgeUnitOfWork({}, sources)
        hk_entries.append(uow)
        return uow

    projection = LyricsVersionProjectionService(lambda: FakeMusicCatalogUnitOfWork({}), hk_factory)
    work_id = uuid7()
    first = _lyrics_version(work_id, allowed_version.id, "First body")
    second = _lyrics_version(work_id, withheld_version.id, "Second body")
    missing = _lyrics_version(work_id, uuid7(), "Missing source body")

    disclosures = await projection.disclose_bodies_for_versions((first, second, missing))

    assert len(hk_entries) == 1
    assert hk_entries[0].enter_count == 1
    assert disclosures[0].body == "First body"
    assert disclosures[0].body_unavailable_reason is None
    assert disclosures[1].body is None
    assert disclosures[1].body_unavailable_reason == RIGHTS_RESTRICTED_REASON
    assert disclosures[2].body is None
    assert disclosures[2].body_unavailable_reason == RIGHTS_RESTRICTED_REASON


@pytest.mark.asyncio
async def test_disclose_bodies_for_versions_empty_skips_uow() -> None:
    hk_entries: list[FakeHistoricalKnowledgeUnitOfWork] = []

    def hk_factory() -> FakeHistoricalKnowledgeUnitOfWork:
        uow = FakeHistoricalKnowledgeUnitOfWork({}, FakeSourceRepository())
        hk_entries.append(uow)
        return uow

    projection = LyricsVersionProjectionService(lambda: FakeMusicCatalogUnitOfWork({}), hk_factory)

    assert await projection.disclose_bodies_for_versions(()) == []
    assert hk_entries == []


def _lyrics_version(work_id, source_version_id, body: str) -> LyricsVersion:
    return LyricsVersion.create(
        uuid7(),
        work_id,
        source_version_id,
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
            body=body,
            provenance="Editorial review.",
        ),
        editorial_status=EditorialStatus.PUBLISHED,
    )
