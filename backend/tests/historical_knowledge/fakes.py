from typing import TYPE_CHECKING, Self

from roots_of_rhythm.historical_knowledge.domain import EditorialStatus, EvidenceStatus, RecordingOriginClaim
from roots_of_rhythm.historical_knowledge.public import PublicEvidenceReference, PublishedGenreRelationClaims

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.application.ports import (
        ClaimRepository,
        ListeningGuideRepository,
        RecordingOriginClaimRepository,
        SourceRepository,
    )
    from roots_of_rhythm.historical_knowledge.domain import (
        GenreRelationClaim,
        ListeningGuide,
        Source,
        SourceFragment,
        SourceVersion,
    )


class FakeClaimRepository:
    def __init__(self, claims: dict[UUID, GenreRelationClaim]) -> None:
        self._claims = claims

    async def add(self, claim: GenreRelationClaim) -> None:
        self._claims[claim.id] = claim

    async def get(self, claim_id: UUID, *, for_update: bool = False) -> GenreRelationClaim | None:
        return self._claims.get(claim_id)

    async def save(self, claim: GenreRelationClaim) -> None:
        self._claims[claim.id] = claim

    async def mark_deleted(self, claim_id: UUID) -> None:
        self._claims.pop(claim_id, None)

    async def list_by_genre(self, genre_id: UUID) -> list[GenreRelationClaim]:
        return [
            claim
            for claim in self._claims.values()
            if claim.subject_genre_id == genre_id or claim.target_genre_id == genre_id
        ]


class FakePublishedGenreRelationClaimReader:
    def __init__(self, claims: dict[UUID, GenreRelationClaim], sources: "FakeSourceRepository") -> None:
        self._claims = claims
        self._sources = sources

    async def read_for_genre(self, genre_id: UUID) -> PublishedGenreRelationClaims:
        claims = tuple(
            claim
            for claim in self._claims.values()
            if claim.editorial_status is EditorialStatus.PUBLISHED
            and (claim.subject_genre_id == genre_id or claim.target_genre_id == genre_id)
        )
        source_ids = await self._sources.reviewed_source_ids_for_fragments(
            {reference.source_fragment_id for claim in claims for reference in claim.evidence_references}
        )
        return PublishedGenreRelationClaims(
            claims,
            {
                claim.id: tuple(
                    PublicEvidenceReference(
                        source_id=source_id,
                        role=reference.role,
                        locator_text=reference.locator_text,
                        external_url=reference.external_url,
                    )
                    for reference in claim.evidence_references
                    if (source_id := source_ids.get(reference.source_fragment_id)) is not None
                )
                for claim in claims
            },
        )


class StubRecordingOriginClaimRepository:
    def __init__(
        self,
        claims_by_recording: dict[UUID, list[RecordingOriginClaim]] | None = None,
    ) -> None:
        self._claims_by_recording = claims_by_recording or {}

    async def add(self, claim: RecordingOriginClaim) -> None:
        self._claims_by_recording.setdefault(claim.recording_id, []).append(claim)

    async def get(self, claim_id: UUID, *, for_update: bool = False) -> RecordingOriginClaim | None:
        return next(
            (claim for claims in self._claims_by_recording.values() for claim in claims if claim.id == claim_id),
            None,
        )

    async def save(self, claim: RecordingOriginClaim) -> None:
        await self.mark_deleted(claim.id)
        await self.add(claim)

    async def mark_deleted(self, claim_id: UUID) -> None:
        for recording_id, claims in self._claims_by_recording.items():
            self._claims_by_recording[recording_id] = [claim for claim in claims if claim.id != claim_id]

    async def list_supported_published_for_recordings(
        self,
        recording_ids: Collection[UUID],
    ) -> dict[UUID, list[RecordingOriginClaim]]:
        return {
            recording_id: [
                claim
                for claim in self._claims_by_recording.get(recording_id, ())
                if claim.editorial_status is EditorialStatus.PUBLISHED
                and claim.evidence_status is EvidenceStatus.SUPPORTED
            ]
            for recording_id in recording_ids
        }


class FakeSourceRepository:
    def __init__(self) -> None:
        self.sources: dict[UUID, Source] = {}
        self.versions: dict[UUID, SourceVersion] = {}
        self.fragments: dict[UUID, SourceFragment] = {}

    async def add_source(self, source: Source) -> None:
        self.sources[source.id] = source

    async def save_source(self, source: Source) -> None:
        self.sources[source.id] = source

    async def add_version(self, version: SourceVersion) -> None:
        self.versions[version.id] = version

    async def add_fragment(self, fragment: SourceFragment) -> None:
        self.fragments[fragment.id] = fragment

    async def get_source(self, source_id: UUID, *, for_update: bool = False) -> Source | None:
        return self.sources.get(source_id)

    async def get_sources_by_ids(self, source_ids: Collection[UUID]) -> dict[UUID, Source]:
        return {source_id: source for source_id in source_ids if (source := self.sources.get(source_id)) is not None}

    async def get_version(self, version_id: UUID, *, for_update: bool = False) -> SourceVersion | None:
        return self.versions.get(version_id)

    async def get_versions_by_ids(self, version_ids: Collection[UUID]) -> dict[UUID, SourceVersion]:
        return {
            version_id: version for version_id in version_ids if (version := self.versions.get(version_id)) is not None
        }

    async def get_fragment(self, fragment_id: UUID, *, for_update: bool = False) -> SourceFragment | None:
        return self.fragments.get(fragment_id)

    async def get_fragments_by_ids(
        self,
        fragment_ids: Collection[UUID],
        *,
        for_update: bool = False,
    ) -> dict[UUID, SourceFragment]:
        return {
            fragment_id: fragment
            for fragment_id in fragment_ids
            if (fragment := self.fragments.get(fragment_id)) is not None
        }

    async def save_fragment(self, fragment: SourceFragment) -> None:
        self.fragments[fragment.id] = fragment

    async def mark_source_deleted(self, source_id: UUID) -> None:
        self.sources.pop(source_id, None)
        version_ids = [version.id for version in self.versions.values() if version.source_id == source_id]
        for version_id in version_ids:
            self.versions.pop(version_id, None)
        for fragment_id, fragment in list(self.fragments.items()):
            if fragment.source_version_id in version_ids:
                self.fragments.pop(fragment_id, None)

    async def mark_version_deleted(self, version_id: UUID) -> None:
        self.versions.pop(version_id, None)
        for fragment_id, fragment in list(self.fragments.items()):
            if fragment.source_version_id == version_id:
                self.fragments.pop(fragment_id, None)

    async def mark_fragment_deleted(self, fragment_id: UUID) -> None:
        self.fragments.pop(fragment_id, None)

    async def reviewed_source_ids_for_fragments(self, fragment_ids: Collection[UUID]) -> dict[UUID, UUID]:
        from roots_of_rhythm.historical_knowledge.domain import FragmentReviewStatus

        result: dict[UUID, UUID] = {}
        for fragment_id in fragment_ids:
            fragment = self.fragments.get(fragment_id)
            if fragment is None or fragment.review_status is not FragmentReviewStatus.REVIEWED:
                continue
            version = self.versions.get(fragment.source_version_id)
            if version is None:
                continue
            result[fragment_id] = version.source_id
        return result


class StubListeningGuideRepository:
    async def add(self, _guide: ListeningGuide) -> None:
        return None

    async def get(self, _guide_id: UUID, *, for_update: bool = False) -> ListeningGuide | None:
        return None

    async def get_published_for_recording(self, _recording_id: UUID) -> ListeningGuide | None:
        return None

    async def save(self, _guide: ListeningGuide) -> None:
        return None

    async def mark_deleted(self, _guide_id: UUID) -> None:
        return None


class FakeHistoricalKnowledgeUnitOfWork:
    def __init__(self, claims: dict[UUID, GenreRelationClaim], sources: FakeSourceRepository) -> None:
        self.claims: ClaimRepository = FakeClaimRepository(claims)
        self.recording_origin_claims: RecordingOriginClaimRepository = StubRecordingOriginClaimRepository()
        self.listening_guides: ListeningGuideRepository = StubListeningGuideRepository()
        self.sources: SourceRepository = sources
        self.commits = 0
        self.enter_count = 0

    async def __aenter__(self) -> Self:
        self.enter_count += 1
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


class StubHistoricalKnowledgeUnitOfWork:
    def __init__(
        self,
        claims_by_recording: dict[UUID, list[RecordingOriginClaim]] | None = None,
    ) -> None:
        self.claims: ClaimRepository = FakeClaimRepository({})
        self.sources: SourceRepository = FakeSourceRepository()
        self.listening_guides: ListeningGuideRepository = StubListeningGuideRepository()
        self.recording_origin_claims: RecordingOriginClaimRepository = StubRecordingOriginClaimRepository(
            claims_by_recording
        )

    async def __aenter__(self) -> "StubHistoricalKnowledgeUnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None
