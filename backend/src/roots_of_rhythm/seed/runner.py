from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.application import ClaimService, SourceService
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceStatus,
    FragmentReviewStatus,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus as ClaimEditorialStatus,
)
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.music_catalog.application import (
    ClassificationAssignmentService,
    GenreService,
    GenreUnitOfWorkStatusLookup,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import EditorialStatus as PersonEditorialStatus
from roots_of_rhythm.people_catalog.domain import PersonContent
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork


class CorpusSeedRunner:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._music_uow: Callable[[], SqlAlchemyMusicCatalogUnitOfWork] = lambda: SqlAlchemyMusicCatalogUnitOfWork(
            session_factory
        )
        self._people_uow: Callable[[], PeopleCatalogUnitOfWork] = lambda: SqlAlchemyPeopleCatalogUnitOfWork(
            session_factory
        )
        self._hk_uow: Callable[[], HistoricalKnowledgeUnitOfWork] = lambda: SqlAlchemyHistoricalKnowledgeUnitOfWork(
            session_factory
        )
        self._genres = GenreService(self._music_uow)
        self._persons = PersonService(self._people_uow)
        self._assignments = ClassificationAssignmentService(self._music_uow, self._person_is_published)
        self._sources = SourceService(self._hk_uow)
        self._claims: ClaimService | None = None

    async def run(self) -> None:
        self._claims = ClaimService(
            self._hk_uow,
            GenreUnitOfWorkStatusLookup(self._music_uow),
        )
        await self._ensure_sources()
        await self._ensure_genres()
        await self._ensure_persons()
        await self._ensure_assignments()
        await self._ensure_claims()

    async def _ensure_sources(self) -> None:
        await self._ensure_source(
            data.SMITHSONIAN_SOURCE_ID,
            data.SMITHSONIAN_TITLE,
            responsible_organization=data.SMITHSONIAN_RESPONSIBLE_ORGANIZATION,
            external_url=data.SMITHSONIAN_EXTERNAL_URL,
        )
        await self._ensure_version(
            data.SMITHSONIAN_SOURCE_ID,
            data.SMITHSONIAN_VERSION_ID,
            data.SOURCE_VERSION_LABEL,
        )
        await self._ensure_source(
            data.LOC_SOURCE_ID,
            data.LOC_TITLE,
            responsible_organization=data.LOC_RESPONSIBLE_ORGANIZATION,
            external_url=data.LOC_EXTERNAL_URL,
        )
        await self._ensure_version(
            data.LOC_SOURCE_ID,
            data.LOC_VERSION_ID,
            data.SOURCE_VERSION_LABEL,
        )
        await self._ensure_reviewed_fragment(
            data.SMITHSONIAN_VERSION_ID,
            data.JAZZ_INTRO_FRAGMENT_ID,
            locator_text="Введение в Jazz",
            external_url=data.JAZZ_INTRO_URL,
        )
        await self._ensure_reviewed_fragment(
            data.SMITHSONIAN_VERSION_ID,
            data.JAZZ_BLUES_FRAGMENT_ID,
            locator_text="Jazz и Blues",
            external_url=data.JAZZ_BLUES_URL,
        )
        await self._ensure_reviewed_fragment(
            data.SMITHSONIAN_VERSION_ID,
            data.FOLKLIFE_RNB_FRAGMENT_ID,
            locator_text="История Rhythm and Blues",
            external_url=data.FOLKLIFE_RNB_URL,
        )
        await self._ensure_reviewed_fragment(
            data.LOC_VERSION_ID,
            data.LOC_RNB_FRAGMENT_ID,
            locator_text="Rhythm and Blues",
            external_url=data.LOC_RNB_URL,
        )

    async def _ensure_genres(self) -> None:
        await self._ensure_published_genre(data.JAZZ_ID, data.JAZZ_CONTENT)
        await self._ensure_published_genre(data.SWING_ID, data.SWING_CONTENT)
        await self._ensure_published_genre(data.JUMP_BLUES_ID, data.JUMP_BLUES_CONTENT)

    async def _ensure_claims(self) -> None:
        claims = self._claims
        if claims is None:
            raise RuntimeError("ClaimService is not initialized; call run()")
        await self._ensure_published_claim(
            claims,
            claim_id=data.SWING_FROM_JAZZ_CLAIM_ID,
            subject_genre_id=data.SWING_ID,
            target_genre_id=data.JAZZ_ID,
            relation_type=data.SWING_FROM_JAZZ_RELATION,
            explanation=data.SWING_FROM_JAZZ_EXPLANATION,
            temporal=data.SWING_FROM_JAZZ_TEMPORAL,
            geographic=data.SWING_FROM_JAZZ_GEOGRAPHIC,
            provenance=data.SWING_FROM_JAZZ_PROVENANCE,
            evidence_status=data.SWING_FROM_JAZZ_EVIDENCE_STATUS,
            evidence=data.SWING_FROM_JAZZ_EVIDENCE,
        )
        await self._ensure_published_claim(
            claims,
            claim_id=data.SWING_TO_JUMP_CLAIM_ID,
            subject_genre_id=data.SWING_ID,
            target_genre_id=data.JUMP_BLUES_ID,
            relation_type=data.SWING_TO_JUMP_RELATION,
            explanation=data.SWING_TO_JUMP_EXPLANATION,
            temporal=data.SWING_TO_JUMP_TEMPORAL,
            geographic=data.SWING_TO_JUMP_GEOGRAPHIC,
            provenance=data.SWING_TO_JUMP_PROVENANCE,
            evidence_status=data.SWING_TO_JUMP_EVIDENCE_STATUS,
            evidence=data.SWING_TO_JUMP_EVIDENCE,
        )

    async def _ensure_source(
        self,
        source_id: UUID,
        title: str,
        *,
        author: str | None = None,
        responsible_organization: str | None = None,
        publication: str | None = None,
        publication_date: str | None = None,
        external_url: str | None = None,
    ) -> None:
        async with self._hk_uow() as uow:
            existing = await uow.sources.get_source(source_id)
        if existing is not None:
            return
        await self._sources.create_source(
            title,
            author=author,
            responsible_organization=responsible_organization,
            publication=publication,
            publication_date=publication_date,
            external_url=external_url,
            source_id=source_id,
        )

    async def _ensure_version(self, source_id: UUID, version_id: UUID, label: str) -> None:
        async with self._hk_uow() as uow:
            existing = await uow.sources.get_version(version_id)
        if existing is not None:
            return
        await self._sources.create_version(source_id, label, version_id=version_id)

    async def _ensure_reviewed_fragment(
        self,
        source_version_id: UUID,
        fragment_id: UUID,
        *,
        locator_text: str,
        external_url: str,
    ) -> None:
        async with self._hk_uow() as uow:
            existing = await uow.sources.get_fragment(fragment_id)
        if existing is None:
            await self._sources.create_fragment(
                source_version_id,
                locator_text=locator_text,
                external_url=external_url,
                fragment_id=fragment_id,
            )
            await self._sources.mark_fragment_reviewed(fragment_id)
            return
        if existing.review_status is not FragmentReviewStatus.REVIEWED:
            await self._sources.mark_fragment_reviewed(fragment_id)

    async def _ensure_published_genre(self, genre_id: UUID, content: ClassificationContent) -> None:
        async with self._music_uow() as uow:
            existing = await uow.genres.get(genre_id)
        if existing is None:
            await self._genres.create(content, genre_id=genre_id)
            await self._genres.publish(genre_id)
            return
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._genres.publish(genre_id)

    async def _ensure_persons(self) -> None:
        for person_id, name in data.SEED_PERFORMERS:
            await self._ensure_published_person(person_id, name)

    async def _ensure_published_person(self, person_id: UUID, name: str) -> None:
        async with self._people_uow() as uow:
            existing = await uow.persons.get(person_id)
        if existing is None:
            await self._persons.create(PersonContent.create(name), person_id=person_id)
            await self._persons.publish(person_id)
            return
        if existing.editorial_status is not PersonEditorialStatus.PUBLISHED:
            await self._persons.publish(person_id)

    async def _ensure_assignments(self) -> None:
        for assignment_id, person_id, genre_id, explanation, provenance in data.SEED_PERSON_GENRE_ASSIGNMENTS:
            await self._ensure_published_assignment(
                assignment_id,
                person_id,
                genre_id,
                explanation=explanation,
                provenance=provenance,
            )

    async def _ensure_published_assignment(
        self,
        assignment_id: UUID,
        person_id: UUID,
        genre_id: UUID,
        *,
        explanation: str,
        provenance: str,
    ) -> None:
        async with self._music_uow() as uow:
            existing = await uow.assignments.get(assignment_id)
        if existing is None:
            await self._assignments.create_for_person(
                person_id,
                genre_id,
                explanation=explanation,
                provenance=provenance,
                assignment_id=assignment_id,
            )
            await self._assignments.publish(assignment_id)
            return
        if existing.explanation != explanation or existing.provenance != provenance:
            await self._assignments.replace_content(
                assignment_id,
                explanation=explanation,
                claim_id=existing.claim_id,
                provenance=provenance,
                evidence_status=existing.evidence_status,
            )
        if existing.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._assignments.publish(assignment_id)

    async def _person_is_published(self, person_id: UUID) -> bool:
        async with self._people_uow() as uow:
            return await uow.persons.get_published(person_id) is not None

    async def _ensure_published_claim(
        self,
        claims: ClaimService,
        *,
        claim_id: UUID,
        subject_genre_id: UUID,
        target_genre_id: UUID,
        relation_type: RelationType,
        explanation: str,
        temporal: HistoricalPeriod,
        geographic: GeographicContext,
        provenance: ClaimProvenance,
        evidence_status: EvidenceStatus,
        evidence: tuple[ClaimEvidenceReference, ...],
    ) -> None:
        async with self._hk_uow() as uow:
            existing = await uow.claims.get(claim_id)
        if existing is not None and existing.editorial_status is ClaimEditorialStatus.PUBLISHED:
            return
        if existing is None:
            await claims.create_draft(
                subject_genre_id,
                target_genre_id,
                relation_type,
                claim_id=claim_id,
            )
        await claims.replace_content(
            claim_id,
            explanation=explanation,
            temporal=temporal,
            geographic=geographic,
            provenance=provenance,
            evidence_status=evidence_status,
        )
        await claims.replace_evidence(claim_id, evidence)
        await claims.publish(claim_id)
