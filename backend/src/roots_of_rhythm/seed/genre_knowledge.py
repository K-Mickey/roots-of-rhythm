"""Genre concepts, editorial sources, and historical genre relations."""

from typing import TYPE_CHECKING
from uuid import UUID

from roots_of_rhythm.historical_knowledge.application import (
    CreateGenreRelationClaim,
    GenreRelationClaimService,
    PublishGenreRelationClaim,
    SourceService,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.historical_knowledge.infrastructure.claim_repository import SqlAlchemyClaimRepository
from roots_of_rhythm.historical_knowledge.infrastructure.source_repository import SqlAlchemySourceRepository
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope, sqlalchemy_session
from roots_of_rhythm.music_catalog.application import GenreService
from roots_of_rhythm.music_catalog.domain import ClassificationContent
from roots_of_rhythm.music_catalog.infrastructure.repository import SqlAlchemyGenreRepository
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.application.transaction import Transaction
    from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork


# --- Genres -----------------------------------------------------------------
JAZZ_ID = UUID("01a0147a-8508-74b7-9689-e7c079b95327")
SWING_ID = UUID("01a0147a-8508-74b7-9689-e7c133e4e7a5")
JUMP_BLUES_ID = UUID("01a0147a-8508-74b7-9689-e7c272039bac")
COUNTRY_ID = UUID("01a0147a-8508-74b7-9689-e7cd00000001")
RHYTHM_AND_BLUES_ID = UUID("01a0147a-8508-74b7-9689-e7cd00000002")
RHYTHM_AND_BLUES_NAME = "Rhythm and Blues"

JAZZ_CONTENT = ClassificationContent.create(
    "Jazz",
    definition=(
        "Американская музыкальная традиция, выросшая в афроамериканских сообществах: "
        "от раннего jazz через big bands эпохи Swing Era к более поздним стилям."
    ),
)
SWING_CONTENT = ClassificationContent.create(
    "Swing",
    definition=(
        "Стиль Jazz эпохи Swing Era: оркестровые аранжировки big band, танцевальный ритм и импровизирующие солисты."
    ),
)
JUMP_BLUES_CONTENT = ClassificationContent.create(
    "Jump Blues",
    definition=(
        "Компактный послевоенный стиль: swing-ритм и духовые riffs "
        "в соединении с Blues, shuffle и линиями Boogie-Woogie bass."
    ),
)
COUNTRY_CONTENT = ClassificationContent.create(
    "Country",
    definition="Американская музыкальная традиция, связанная с folk, ballad и string-band music.",
)
RHYTHM_AND_BLUES_CONTENT = ClassificationContent.create(
    RHYTHM_AND_BLUES_NAME,
    definition="Афроамериканская популярная музыкальная традиция, объединяющая blues, jazz и gospel influences.",
)

# --- Sources ----------------------------------------------------------------
SMITHSONIAN_SOURCE_ID = UUID("01a0147a-8508-74b7-9689-e7c3052e0e19")
SMITHSONIAN_VERSION_ID = UUID("01a0147a-8508-74b7-9689-e7c4d86d78f9")
LOC_SOURCE_ID = UUID("01a0147a-8508-74b7-9689-e7c58c0b7736")
LOC_VERSION_ID = UUID("01a0147a-8508-74b7-9689-e7c6043bca04")

SMITHSONIAN_TITLE = "Jazz"
SMITHSONIAN_RESPONSIBLE_ORGANIZATION = "Smithsonian Music"
SMITHSONIAN_EXTERNAL_URL = "https://music.si.edu/story/jazz"
LOC_RESPONSIBLE_ORGANIZATION = "Library of Congress"
LOC_EXTERNAL_URL = (
    "https://www.loc.gov/collections/songs-of-america/articles-and-essays/"
    "musical-styles/popular-songs-of-the-day/rhythm-and-blues/"
)
SOURCE_VERSION_LABEL = "web 2026-08"
SIXTEEN_TONS_SOURCE_URL = (
    "https://blogs.loc.gov/now-see-hear/2021/07/"
    "from-the-national-recording-registry-16-tons-by-tennessee-ernie-ford-1955/"
)

# --- Fragments --------------------------------------------------------------
JAZZ_INTRO_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7c7f9e6dc36")
JAZZ_BLUES_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7c8cd1c114b")
FOLKLIFE_RNB_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7c95d709c45")
LOC_RNB_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7ca7a660b98")

JAZZ_INTRO_URL = "https://music.si.edu/story/jazz"
JAZZ_BLUES_URL = "https://music.si.edu/spotlight/african-american-music/jazz-blues"
FOLKLIFE_RNB_URL = "https://folklife.si.edu/magazine/freedom-sounds-tell-it-like-it-is-a-history-of-rhythm-and-blues"
LOC_RNB_URL = (
    "https://www.loc.gov/collections/songs-of-america/articles-and-essays/"
    "musical-styles/popular-songs-of-the-day/rhythm-and-blues/"
)

# --- Claims -----------------------------------------------------------------
SWING_FROM_JAZZ_CLAIM_ID = UUID("01a0147a-8508-74b7-9689-e7cb0316a0f5")
SWING_TO_JUMP_CLAIM_ID = UUID("01a0147a-8508-74b7-9689-e7cc2797195b")

SWING_FROM_JAZZ_EXPLANATION = (
    "Swing сформировался внутри американской джазовой традиции на основе развития "
    "оркестровых аранжировок, ритмической организации и роли импровизирующих солистов. "
    "В 1930-е эти изменения оформились в Swing Era и сделали большие джазовые оркестры "
    "центральной частью массовой танцевальной культуры."
)
SWING_TO_JUMP_EXPLANATION = (
    "Swing был одним из основных входов в формирование Jump Blues. Музыканты перенесли "
    "swing-ритм, духовые riffs и опыт больших оркестров в более компактные составы, "
    "соединив их с Blues, shuffle rhythm и Boogie-Woogie bass lines. Поэтому Jump Blues "
    "нельзя описывать как продолжение только одного Swing."
)

SWING_FROM_JAZZ_TEMPORAL = HistoricalPeriod.create(
    "late 1920s–1930s",
    TemporalBound(1920, TemporalPrecision.LATE_DECADE),
    TemporalBound(1930, TemporalPrecision.DECADE),
)
SWING_TO_JUMP_TEMPORAL = HistoricalPeriod.create(
    "late 1930s–1940s",
    TemporalBound(1930, TemporalPrecision.LATE_DECADE),
    TemporalBound(1940, TemporalPrecision.DECADE),
)

SWING_FROM_JAZZ_GEOGRAPHIC = GeographicContext.create("United States")
SWING_TO_JUMP_GEOGRAPHIC = GeographicContext.create(
    "United States urban African American music scenes",
)

SWING_FROM_JAZZ_PROVENANCE = ClaimProvenance.create(
    "Редакционный синтез материалов Smithsonian Music о Jazz для controlled corpus seed.",
)
SWING_TO_JUMP_PROVENANCE = ClaimProvenance.create(
    "Редакционный синтез Smithsonian Folklife и Library of Congress о Rhythm and Blues для controlled corpus seed.",
)

SWING_FROM_JAZZ_EVIDENCE = (
    ClaimEvidenceReference.create(
        JAZZ_INTRO_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="От Jazz Age к Swing Era",
        external_url=JAZZ_INTRO_URL,
    ),
    ClaimEvidenceReference.create(
        JAZZ_BLUES_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Big bands Swing Era 1930-х",
        external_url=JAZZ_BLUES_URL,
    ),
)
SWING_TO_JUMP_EVIDENCE = (
    ClaimEvidenceReference.create(
        FOLKLIFE_RNB_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Jump Blues как смесь Swing и Blues",
        external_url=FOLKLIFE_RNB_URL,
    ),
    ClaimEvidenceReference.create(
        LOC_RNB_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Ранний R&B и афроамериканский Swing",
        external_url=LOC_RNB_URL,
    ),
)

SWING_FROM_JAZZ_RELATION = RelationType.DEVELOPED_FROM
SWING_TO_JUMP_RELATION = RelationType.CONTRIBUTED_TO_EMERGENCE_OF
SWING_FROM_JAZZ_EVIDENCE_STATUS = EvidenceStatus.SUPPORTED
SWING_TO_JUMP_EVIDENCE_STATUS = EvidenceStatus.SUPPORTED


class GenreKnowledgeSeed:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._music_uow: Callable[[], SqlAlchemyMusicCatalogUnitOfWork] = lambda: SqlAlchemyMusicCatalogUnitOfWork(
            session_factory
        )
        self._hk_uow: Callable[[], HistoricalKnowledgeUnitOfWork] = lambda: SqlAlchemyHistoricalKnowledgeUnitOfWork(
            session_factory
        )
        self._genres = GenreService(self._music_uow)
        self._sources = SourceService(self._hk_uow)
        transaction_scope = SqlAlchemyTransactionScope(session_factory)

        def claim_repository(transaction: "Transaction") -> SqlAlchemyClaimRepository:
            return SqlAlchemyClaimRepository(sqlalchemy_session(transaction))

        def source_repository(transaction: "Transaction") -> SqlAlchemySourceRepository:
            return SqlAlchemySourceRepository(sqlalchemy_session(transaction))

        def genre_repository(transaction: "Transaction") -> SqlAlchemyGenreRepository:
            return SqlAlchemyGenreRepository(sqlalchemy_session(transaction))

        self._claims = GenreRelationClaimService(
            transaction_scope,
            claim_repository,
            source_repository,
        )
        self._create_claim = CreateGenreRelationClaim(
            transaction_scope,
            claim_repository,
            genre_repository,
        )
        self._publish_claim = PublishGenreRelationClaim(
            transaction_scope,
            claim_repository,
            source_repository,
            genre_repository,
        )

    async def run(self) -> None:
        await self._ensure_sources()
        await self._ensure_genres()
        await self._ensure_claims()

    async def _ensure_sources(self) -> None:
        await self._ensure_source(
            SMITHSONIAN_SOURCE_ID,
            SMITHSONIAN_TITLE,
            responsible_organization=SMITHSONIAN_RESPONSIBLE_ORGANIZATION,
            external_url=SMITHSONIAN_EXTERNAL_URL,
        )
        await self._ensure_version(
            SMITHSONIAN_SOURCE_ID,
            SMITHSONIAN_VERSION_ID,
            SOURCE_VERSION_LABEL,
        )
        await self._ensure_source(
            LOC_SOURCE_ID,
            RHYTHM_AND_BLUES_NAME,
            responsible_organization=LOC_RESPONSIBLE_ORGANIZATION,
            external_url=LOC_EXTERNAL_URL,
        )
        await self._ensure_version(
            LOC_SOURCE_ID,
            LOC_VERSION_ID,
            SOURCE_VERSION_LABEL,
        )
        await self._ensure_reviewed_fragment(
            SMITHSONIAN_VERSION_ID,
            JAZZ_INTRO_FRAGMENT_ID,
            locator_text="Введение в Jazz",
            external_url=JAZZ_INTRO_URL,
        )
        await self._ensure_reviewed_fragment(
            SMITHSONIAN_VERSION_ID,
            JAZZ_BLUES_FRAGMENT_ID,
            locator_text="Jazz и Blues",
            external_url=JAZZ_BLUES_URL,
        )
        await self._ensure_reviewed_fragment(
            SMITHSONIAN_VERSION_ID,
            FOLKLIFE_RNB_FRAGMENT_ID,
            locator_text="История Rhythm and Blues",
            external_url=FOLKLIFE_RNB_URL,
        )
        await self._ensure_reviewed_fragment(
            LOC_VERSION_ID,
            LOC_RNB_FRAGMENT_ID,
            locator_text=RHYTHM_AND_BLUES_NAME,
            external_url=LOC_RNB_URL,
        )

    async def _ensure_genres(self) -> None:
        await self._ensure_published_genre(JAZZ_ID, JAZZ_CONTENT)
        await self._ensure_published_genre(SWING_ID, SWING_CONTENT)
        await self._ensure_published_genre(JUMP_BLUES_ID, JUMP_BLUES_CONTENT)
        await self._ensure_published_genre(COUNTRY_ID, COUNTRY_CONTENT)
        await self._ensure_published_genre(RHYTHM_AND_BLUES_ID, RHYTHM_AND_BLUES_CONTENT)

    async def _ensure_claims(self) -> None:
        claims = self._claims
        await self._ensure_published_claim(
            claims,
            claim_id=SWING_FROM_JAZZ_CLAIM_ID,
            subject_genre_id=SWING_ID,
            target_genre_id=JAZZ_ID,
            relation_type=SWING_FROM_JAZZ_RELATION,
            explanation=SWING_FROM_JAZZ_EXPLANATION,
            temporal=SWING_FROM_JAZZ_TEMPORAL,
            geographic=SWING_FROM_JAZZ_GEOGRAPHIC,
            provenance=SWING_FROM_JAZZ_PROVENANCE,
            evidence_status=SWING_FROM_JAZZ_EVIDENCE_STATUS,
            evidence=SWING_FROM_JAZZ_EVIDENCE,
        )
        await self._ensure_published_claim(
            claims,
            claim_id=SWING_TO_JUMP_CLAIM_ID,
            subject_genre_id=SWING_ID,
            target_genre_id=JUMP_BLUES_ID,
            relation_type=SWING_TO_JUMP_RELATION,
            explanation=SWING_TO_JUMP_EXPLANATION,
            temporal=SWING_TO_JUMP_TEMPORAL,
            geographic=SWING_TO_JUMP_GEOGRAPHIC,
            provenance=SWING_TO_JUMP_PROVENANCE,
            evidence_status=SWING_TO_JUMP_EVIDENCE_STATUS,
            evidence=SWING_TO_JUMP_EVIDENCE,
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
        if not existing.is_reviewed:
            await self._sources.mark_fragment_reviewed(fragment_id)

    async def _ensure_published_genre(self, genre_id: UUID, content: ClassificationContent) -> None:
        async with self._music_uow() as uow:
            existing = await uow.genres.get(genre_id)
        if existing is None:
            await self._genres.create(content, genre_id=genre_id)
            await self._genres.publish(genre_id)
            return
        if not existing.is_published:
            await self._genres.publish(genre_id)

    async def _ensure_published_claim(
        self,
        claims: GenreRelationClaimService,
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
        if existing is not None and existing.is_published:
            return
        if existing is None:
            await self._create_claim.execute(
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
        await self._publish_claim.execute(claim_id)
