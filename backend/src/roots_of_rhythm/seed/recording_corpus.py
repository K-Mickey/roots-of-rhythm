"""Controlled recordings, lyrics, evidence, and listening-guide corpus."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from roots_of_rhythm.historical_knowledge.application import (
    CreateRecordingOriginClaim,
    ListeningGuideService,
    PublishListeningGuide,
    PublishRecordingOriginClaim,
    RecordingOriginClaimService,
    ReplaceListeningGuideObservations,
    SourceService,
)
from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    GeographicContext,
    HistoricalPeriod,
    ListeningGuide,
    ListeningObservation,
    RecordingOriginPredicate,
    SourceAccessPolicy,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.historical_knowledge.domain import EditorialStatus as ClaimEditorialStatus
from roots_of_rhythm.historical_knowledge.infrastructure.listening_guide_repository import (
    SqlAlchemyListeningGuideRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.recording_origin_claim_repository import (
    SqlAlchemyRecordingOriginClaimRepository,
)
from roots_of_rhythm.historical_knowledge.infrastructure.source_repository import SqlAlchemySourceRepository
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope, sqlalchemy_session
from roots_of_rhythm.music_catalog.application import (
    LyricsVersionRelationService,
    LyricsVersionService,
    PublishRecording,
    RecordingService,
    ReplaceRecordingContent,
)
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    ClassificationAssignment,
    ClassificationTargetKind,
    ExistencePeriod,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionContent,
    LyricsVersionRelationContent,
    LyricsVersionRelationType,
    RecordingContent,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingLyricsUsage,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
)
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from roots_of_rhythm.music_catalog.domain import EvidenceStatus as MusicEvidenceStatus
from roots_of_rhythm.music_catalog.domain import TemporalBound as MusicTemporalBound
from roots_of_rhythm.music_catalog.domain import TemporalPrecision as MusicTemporalPrecision
from roots_of_rhythm.music_catalog.infrastructure.group_repository import SqlAlchemyGroupRepository
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_repository import SqlAlchemyLyricsVersionRepository
from roots_of_rhythm.music_catalog.infrastructure.musical_work_repository import SqlAlchemyMusicalWorkRepository
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.infrastructure.repository import SqlAlchemyPersonRepository
from roots_of_rhythm.seed.genre_knowledge import COUNTRY_ID, RHYTHM_AND_BLUES_ID, SOURCE_VERSION_LABEL
from roots_of_rhythm.seed.musical_works import NOBODY_KNOWS_TROUBLE_ID, SIXTEEN_TONS_ID
from roots_of_rhythm.seed.people_and_groups import (
    LOUIS_ARMSTRONG_ID,
    MARIAN_ANDERSON_ID,
    MERLE_TRAVIS_ID,
    SEED_ASSIGNMENT_PROVENANCE,
    STEVIE_WONDER_ID,
    TENNESSEE_ERNIE_FORD_ID,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.application.transaction import Transaction
    from roots_of_rhythm.historical_knowledge.application.ports import HistoricalKnowledgeUnitOfWork


# --- Source -----------------------------------------------------------------
SIXTEEN_TONS_SOURCE_ID = UUID("01a0147a-8508-74b7-9689-e7cd00000003")
SIXTEEN_TONS_SOURCE_VERSION_ID = UUID("01a0147a-8508-74b7-9689-e7cd00000004")
SIXTEEN_TONS_SOURCE_TITLE = "Sixteen Tons — Tennessee Ernie Ford (1955)"
SIXTEEN_TONS_SOURCE_AUTHOR = "Ted Olson"
SIXTEEN_TONS_SOURCE_URL = (
    "https://blogs.loc.gov/now-see-hear/2021/07/"
    "from-the-national-recording-registry-16-tons-by-tennessee-ernie-ford-1955/"
)
SIXTEEN_TONS_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7cd00000005")
SIXTEEN_TONS_FRAGMENT_URL = SIXTEEN_TONS_SOURCE_URL

# --- Sixteen Tons Recording corpus -----------------------------------------
MERLE_TRAVIS_RECORDING_ID = UUID("01a01a72-4a01-7000-8000-000000000001")
TENNESSEE_ERNIE_FORD_RECORDING_ID = UUID("01a01a72-4a01-7000-8000-000000000002")
STEVIE_WONDER_RECORDING_ID = UUID("01a01a72-4a01-7000-8000-000000000003")

MERLE_TRAVIS_RECORDING_CREDIT_ID = UUID("01a01a72-4a01-7000-8000-000000000011")
FORD_RECORDING_CREDIT_ID = UUID("01a01a72-4a01-7000-8000-000000000012")
STEVIE_RECORDING_CREDIT_ID = UUID("01a01a72-4a01-7000-8000-000000000013")
MERLE_TRAVIS_WORK_USAGE_ID = UUID("01a01a72-4a01-7000-8000-000000000021")
FORD_WORK_USAGE_ID = UUID("01a01a72-4a01-7000-8000-000000000022")
STEVIE_WORK_USAGE_ID = UUID("01a01a72-4a01-7000-8000-000000000023")
FORD_LYRICS_USAGE_ID = UUID("01a01a72-4a01-7000-8000-000000000024")

SIXTEEN_TONS_EN_LYRICS_ID = UUID("01a01a72-4a01-7000-8000-000000000031")
SIXTEEN_TONS_RU_READING_ID = UUID("01a01a72-4a01-7000-8000-000000000032")
SIXTEEN_TONS_TRANSLATION_RELATION_ID = UUID("01a01a72-4a01-7000-8000-000000000033")

SIXTEEN_TONS_EN_LYRICS = LyricsVersionContent.create(
    language_tag="en",
    usage_kind=LyricsUsageKind.PERFORMABLE,
    creation_method=LyricsCreationMethod.ORIGINAL,
    label="English",
    provenance="Metadata only; copyrighted lyrics body is intentionally omitted.",
)
SIXTEEN_TONS_RU_READING = LyricsVersionContent.create(
    language_tag="ru",
    usage_kind=LyricsUsageKind.READING_TRANSLATION,
    creation_method=LyricsCreationMethod.MACHINE_TRANSLATION,
    label="Русский перевод",
    provenance="Machine-translation metadata seed; body is intentionally omitted.",
)
SIXTEEN_TONS_TRANSLATION_RELATION = LyricsVersionRelationContent.create(
    relation_type=LyricsVersionRelationType.TRANSLATION_OF,
    provenance="Controlled corpus translation metadata.",
)


def _recording_content(
    performer_id: UUID,
    credit_id: UUID,
    work_usage_id: UUID,
    *,
    year: int | None,
    lyrics_usage: bool = False,
) -> RecordingContent:
    return RecordingContent.create(
        "Sixteen Tons",
        recorded_period=(
            None
            if year is None
            else ExistencePeriod.create(start=MusicTemporalBound(year, MusicTemporalPrecision.EXACT_YEAR))
        ),
        recording_credits=(
            RecordingCredit.create(
                credit_id,
                RecordingCreditTargetKind.PERSON,
                performer_id,
                BillingRole.PRIMARY,
                credited_as=None,
            ),
        ),
        work_usages=(
            RecordingWorkUsage.create(
                work_usage_id,
                SIXTEEN_TONS_ID,
                RecordingWorkUsageKind.COMPLETE,
            ),
        ),
        lyrics_usages=(
            (RecordingLyricsUsage.create(FORD_LYRICS_USAGE_ID, SIXTEEN_TONS_EN_LYRICS_ID),) if lyrics_usage else ()
        ),
    )


SEED_RECORDINGS: tuple[tuple[UUID, RecordingContent], ...] = (
    (
        MERLE_TRAVIS_RECORDING_ID,
        _recording_content(MERLE_TRAVIS_ID, MERLE_TRAVIS_RECORDING_CREDIT_ID, MERLE_TRAVIS_WORK_USAGE_ID, year=1946),
    ),
    (
        TENNESSEE_ERNIE_FORD_RECORDING_ID,
        _recording_content(
            TENNESSEE_ERNIE_FORD_ID,
            FORD_RECORDING_CREDIT_ID,
            FORD_WORK_USAGE_ID,
            year=1955,
            lyrics_usage=True,
        ),
    ),
    (
        STEVIE_WONDER_RECORDING_ID,
        _recording_content(STEVIE_WONDER_ID, STEVIE_RECORDING_CREDIT_ID, STEVIE_WORK_USAGE_ID, year=None),
    ),
)

MERLE_COUNTRY_ASSIGNMENT_ID = UUID("01a01a72-4a01-7000-8000-000000000041")
FORD_COUNTRY_ASSIGNMENT_ID = UUID("01a01a72-4a01-7000-8000-000000000042")
STEVIE_RNB_ASSIGNMENT_ID = UUID("01a01a72-4a01-7000-8000-000000000043")
SEED_RECORDING_GENRE_ASSIGNMENTS: tuple[tuple[UUID, UUID, UUID, str], ...] = (
    (
        MERLE_COUNTRY_ASSIGNMENT_ID,
        MERLE_TRAVIS_RECORDING_ID,
        COUNTRY_ID,
        "Merle Travis's Sixteen Tons recording is classified as Country.",
    ),
    (
        FORD_COUNTRY_ASSIGNMENT_ID,
        TENNESSEE_ERNIE_FORD_RECORDING_ID,
        COUNTRY_ID,
        "Tennessee Ernie Ford's Sixteen Tons recording is classified as Country.",
    ),
    (
        STEVIE_RNB_ASSIGNMENT_ID,
        STEVIE_WONDER_RECORDING_ID,
        RHYTHM_AND_BLUES_ID,
        "Stevie Wonder's Sixteen Tons recording is classified as Rhythm and Blues.",
    ),
)

MERLE_FIRST_RECORDING_CLAIM_ID = UUID("01a01a72-4a01-7000-8000-000000000051")
MERLE_FIRST_RECORDING_PREDICATE = RecordingOriginPredicate.FIRST_RECORDING_OF
MERLE_FIRST_RECORDING_TEMPORAL = HistoricalPeriod.create(
    "1946",
    TemporalBound(1946, TemporalPrecision.EXACT_YEAR),
    TemporalBound(1946, TemporalPrecision.EXACT_YEAR),
)
MERLE_FIRST_RECORDING_GEOGRAPHIC = GeographicContext.create("United States")
MERLE_FIRST_RECORDING_PROVENANCE = ClaimProvenance.create(
    "Редакционный синтез Library of Congress о происхождении Sixteen Tons."
)
MERLE_FIRST_RECORDING_EVIDENCE = (
    ClaimEvidenceReference.create(
        SIXTEEN_TONS_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Merle Travis wrote and recorded Sixteen Tons in 1946",
        external_url=SIXTEEN_TONS_FRAGMENT_URL,
    ),
)

FORD_LISTENING_GUIDE_ID = UUID("01a01a72-4a01-7000-8000-000000000061")
FORD_LISTENING_OBSERVATION_ID = UUID("01a01a72-4a01-7000-8000-000000000062")
SEED_EDITOR_ID = UUID("01a01a72-4a01-7000-8000-000000000063")
FORD_LISTENING_OBSERVATIONS = (
    ListeningObservation.create(
        "Щелчки пальцами и пульс",
        "Обратите внимание, как щелчки пальцами задают темп и поддерживают сдержанную аранжировку.",
        SEED_EDITOR_ID,
        datetime(2026, 8, 30, tzinfo=UTC),
        observation_id=FORD_LISTENING_OBSERVATION_ID,
        context="Tennessee Ernie Ford — Sixteen Tons",
    ),
)
FORD_LISTENING_GUIDE = ListeningGuide.create_draft(
    TENNESSEE_ERNIE_FORD_RECORDING_ID,
    FORD_LISTENING_OBSERVATIONS,
    guide_id=FORD_LISTENING_GUIDE_ID,
)

# --- Public-domain lyrics recording corpus ---------------------------------
PUBLIC_DOMAIN_SOURCE_ID = UUID("01a01a72-5a01-7000-8000-000000000001")
PUBLIC_DOMAIN_SOURCE_VERSION_ID = UUID("01a01a72-5a01-7000-8000-000000000002")
ENGLISH_LYRICS_ID = UUID("01a01a72-5a01-7000-8000-000000000003")
RUSSIAN_TRANSLATION_ID = UUID("01a01a72-5a01-7000-8000-000000000004")
TRANSLATION_RELATION_ID = UUID("01a01a72-5a01-7000-8000-000000000005")

MARIAN_RECORDING_ID = UUID("01a01a72-5a01-7000-8000-000000000011")
LOUIS_RECORDING_ID = UUID("01a01a72-5a01-7000-8000-000000000012")
MARIAN_CREDIT_ID = UUID("01a01a72-5a01-7000-8000-000000000013")
LOUIS_CREDIT_ID = UUID("01a01a72-5a01-7000-8000-000000000014")
MARIAN_WORK_USAGE_ID = UUID("01a01a72-5a01-7000-8000-000000000015")
LOUIS_WORK_USAGE_ID = UUID("01a01a72-5a01-7000-8000-000000000016")

PUBLIC_DOMAIN_SOURCE_URL = "https://www.loc.gov/collections/songs-of-america/articles-and-essays/timeline/1850-to-1899/"

ENGLISH_BODY = """Nobody knows the trouble I've seen,
Nobody knows but Jesus;
Nobody knows the trouble I've seen,
Glory, hallelujah!

Sometimes I'm up, sometimes I'm down,
Oh, yes, Lord;
Sometimes I'm almost to the ground,
Oh, yes, Lord.

Although you see me going along,
Oh, yes, Lord;
I have my trials here below,
Oh, yes, Lord.

If you get there before I do,
Oh, yes, Lord;
Tell all my friends I'm coming too,
Oh, yes, Lord."""

RUSSIAN_BODY = """Никто не знает бед, что я познал,
Никто не знает — только Иисус;
Никто не знает бед, что я познал,
Слава, аллилуйя!

То я наверху, то я внизу,
О да, Господь;
Порой я почти лежу на земле,
О да, Господь.

Пусть видят, что я продолжаю путь,
О да, Господь;
Здесь, внизу, мне выпали испытания,
О да, Господь.

Если ты придёшь туда прежде меня,
О да, Господь;
Скажи всем друзьям, что я тоже иду,
О да, Господь."""

ENGLISH_LYRICS = LyricsVersionContent.create(
    language_tag="en",
    usage_kind=LyricsUsageKind.PERFORMABLE,
    creation_method=LyricsCreationMethod.ORIGINAL,
    label="Traditional English text",
    body=ENGLISH_BODY,
    provenance="Public-domain traditional text, based on the version published in 1867.",
)
RUSSIAN_TRANSLATION = LyricsVersionContent.create(
    language_tag="ru",
    usage_kind=LyricsUsageKind.READING_TRANSLATION,
    creation_method=LyricsCreationMethod.MACHINE_TRANSLATION,
    label="Русский перевод",
    body=RUSSIAN_BODY,
    provenance="Project-created machine reading translation of public-domain lyrics.",
)
TRANSLATION_RELATION = LyricsVersionRelationContent.create(
    relation_type=LyricsVersionRelationType.TRANSLATION_OF,
    provenance="Controlled corpus relation between the public-domain text and its reading translation.",
)


def _public_domain_recording(
    recording_id: UUID,
    performer_id: UUID,
    credit_id: UUID,
    work_usage_id: UUID,
    year: int,
) -> tuple[UUID, RecordingContent]:
    return (
        recording_id,
        RecordingContent.create(
            "Nobody Knows the Trouble I've Seen",
            recorded_period=ExistencePeriod.create(start=MusicTemporalBound(year, MusicTemporalPrecision.EXACT_YEAR)),
            recording_credits=(
                RecordingCredit.create(
                    credit_id,
                    RecordingCreditTargetKind.PERSON,
                    performer_id,
                    BillingRole.PRIMARY,
                ),
            ),
            work_usages=(
                RecordingWorkUsage.create(
                    work_usage_id,
                    NOBODY_KNOWS_TROUBLE_ID,
                    RecordingWorkUsageKind.COMPLETE,
                ),
            ),
        ),
    )


PUBLIC_DOMAIN_RECORDINGS = (
    _public_domain_recording(
        MARIAN_RECORDING_ID,
        MARIAN_ANDERSON_ID,
        MARIAN_CREDIT_ID,
        MARIAN_WORK_USAGE_ID,
        1924,
    ),
    _public_domain_recording(
        LOUIS_RECORDING_ID,
        LOUIS_ARMSTRONG_ID,
        LOUIS_CREDIT_ID,
        LOUIS_WORK_USAGE_ID,
        1938,
    ),
)


class RecordingCorpusSeed:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._music_uow: Callable[[], SqlAlchemyMusicCatalogUnitOfWork] = lambda: SqlAlchemyMusicCatalogUnitOfWork(
            session_factory
        )
        self._hk_uow: Callable[[], HistoricalKnowledgeUnitOfWork] = lambda: SqlAlchemyHistoricalKnowledgeUnitOfWork(
            session_factory
        )
        self._sources = SourceService(self._hk_uow)
        self._lyrics_versions = LyricsVersionService(self._music_uow)
        self._lyrics_relations = LyricsVersionRelationService(self._music_uow)
        transaction_scope = SqlAlchemyTransactionScope(session_factory)

        def recording_repository_factory(transaction: "Transaction") -> SqlAlchemyRecordingRepository:
            return SqlAlchemyRecordingRepository(sqlalchemy_session(transaction))

        def origin_claim_repository_factory(transaction: "Transaction") -> SqlAlchemyRecordingOriginClaimRepository:
            return SqlAlchemyRecordingOriginClaimRepository(sqlalchemy_session(transaction))

        def listening_guide_repository_factory(transaction: "Transaction") -> SqlAlchemyListeningGuideRepository:
            return SqlAlchemyListeningGuideRepository(sqlalchemy_session(transaction))

        def source_repository_factory(transaction: "Transaction") -> SqlAlchemySourceRepository:
            return SqlAlchemySourceRepository(sqlalchemy_session(transaction))

        def work_repository_factory(transaction: "Transaction") -> SqlAlchemyMusicalWorkRepository:
            return SqlAlchemyMusicalWorkRepository(sqlalchemy_session(transaction))

        self._recordings = RecordingService(transaction_scope, recording_repository_factory)
        self._publish_recording = PublishRecording(
            transaction_scope=transaction_scope,
            recording_repository_factory=recording_repository_factory,
            work_repository_factory=lambda transaction: SqlAlchemyMusicalWorkRepository(
                sqlalchemy_session(transaction)
            ),
            lyrics_version_repository_factory=lambda transaction: SqlAlchemyLyricsVersionRepository(
                sqlalchemy_session(transaction)
            ),
            group_repository_factory=lambda transaction: SqlAlchemyGroupRepository(sqlalchemy_session(transaction)),
            person_repository_factory=lambda transaction: SqlAlchemyPersonRepository(sqlalchemy_session(transaction)),
        )
        self._replace_recording_content = ReplaceRecordingContent(
            transaction_scope=transaction_scope,
            recording_repository_factory=recording_repository_factory,
            work_repository_factory=lambda transaction: SqlAlchemyMusicalWorkRepository(
                sqlalchemy_session(transaction)
            ),
            lyrics_version_repository_factory=lambda transaction: SqlAlchemyLyricsVersionRepository(
                sqlalchemy_session(transaction)
            ),
            group_repository_factory=lambda transaction: SqlAlchemyGroupRepository(sqlalchemy_session(transaction)),
            person_repository_factory=lambda transaction: SqlAlchemyPersonRepository(sqlalchemy_session(transaction)),
        )
        self._recording_origin_claims = RecordingOriginClaimService(
            transaction_scope,
            origin_claim_repository_factory,
            source_repository_factory,
        )
        self._create_recording_origin_claim = CreateRecordingOriginClaim(
            transaction_scope,
            origin_claim_repository_factory,
            recording_repository_factory,
            work_repository_factory,
        )
        self._publish_recording_origin_claim = PublishRecordingOriginClaim(
            transaction_scope,
            origin_claim_repository_factory,
            recording_repository_factory,
            work_repository_factory,
            source_repository_factory,
        )
        self._listening_guides = ListeningGuideService(
            transaction_scope,
            listening_guide_repository_factory,
        )
        self._replace_listening_guide_observations = ReplaceListeningGuideObservations(
            transaction_scope,
            listening_guide_repository_factory,
            recording_repository_factory,
        )
        self._publish_listening_guide = PublishListeningGuide(
            transaction_scope,
            listening_guide_repository_factory,
            recording_repository_factory,
        )

    async def run(self) -> None:
        await self._ensure_source_material()
        await self._ensure_lyrics_versions()
        await self._ensure_lyrics_relations()
        await self._ensure_recordings()
        await self._ensure_recording_genre_assignments()
        await self._ensure_recording_origin_claim()
        await self._ensure_listening_guide()

    async def _ensure_source_material(self) -> None:
        await self._ensure_source(
            SIXTEEN_TONS_SOURCE_ID,
            SIXTEEN_TONS_SOURCE_TITLE,
            author=SIXTEEN_TONS_SOURCE_AUTHOR,
            responsible_organization="Library of Congress",
            publication="Now See Hear!",
            external_url=SIXTEEN_TONS_SOURCE_URL,
        )
        await self._ensure_version(SIXTEEN_TONS_SOURCE_ID, SIXTEEN_TONS_SOURCE_VERSION_ID, SOURCE_VERSION_LABEL)
        await self._ensure_reviewed_fragment(
            SIXTEEN_TONS_SOURCE_VERSION_ID,
            SIXTEEN_TONS_FRAGMENT_ID,
            locator_text="История Sixteen Tons и известных записей",
            external_url=SIXTEEN_TONS_FRAGMENT_URL,
        )
        await self._ensure_source(
            PUBLIC_DOMAIN_SOURCE_ID,
            "Slave Songs of the United States",
            responsible_organization="Library of Congress",
            publication="A. Simpson & Co.",
            publication_date="1867",
            external_url=PUBLIC_DOMAIN_SOURCE_URL,
        )
        await self._ensure_version(
            PUBLIC_DOMAIN_SOURCE_ID,
            PUBLIC_DOMAIN_SOURCE_VERSION_ID,
            "1867 first edition",
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
        if existing is None:
            await self._sources.create_source(
                title,
                author=author,
                responsible_organization=responsible_organization,
                publication=publication,
                publication_date=publication_date,
                external_url=external_url,
                access_policy=SourceAccessPolicy.ALLOW_PUBLIC_BODY,
                source_id=source_id,
            )
        elif existing.access_policy is not SourceAccessPolicy.ALLOW_PUBLIC_BODY:
            await self._sources.set_access_policy(source_id, SourceAccessPolicy.ALLOW_PUBLIC_BODY)

    async def _ensure_version(self, source_id: UUID, version_id: UUID, label: str) -> None:
        async with self._hk_uow() as uow:
            existing = await uow.sources.get_version(version_id)
        if existing is None:
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
        elif existing.review_status is not FragmentReviewStatus.REVIEWED:
            await self._sources.mark_fragment_reviewed(fragment_id)

    async def _ensure_lyrics_versions(self) -> None:
        await self._ensure_published_lyrics_version(
            SIXTEEN_TONS_EN_LYRICS_ID,
            SIXTEEN_TONS_EN_LYRICS,
        )
        await self._ensure_published_lyrics_version(
            SIXTEEN_TONS_RU_READING_ID,
            SIXTEEN_TONS_RU_READING,
            requires_review=True,
        )
        await self._ensure_published_lyrics_version(
            ENGLISH_LYRICS_ID,
            ENGLISH_LYRICS,
            work_id=NOBODY_KNOWS_TROUBLE_ID,
            source_version_id=PUBLIC_DOMAIN_SOURCE_VERSION_ID,
        )
        await self._ensure_published_lyrics_version(
            RUSSIAN_TRANSLATION_ID,
            RUSSIAN_TRANSLATION,
            work_id=NOBODY_KNOWS_TROUBLE_ID,
            source_version_id=PUBLIC_DOMAIN_SOURCE_VERSION_ID,
            requires_review=True,
        )

    async def _ensure_published_lyrics_version(
        self,
        version_id: UUID,
        content: LyricsVersionContent,
        *,
        work_id: UUID = SIXTEEN_TONS_ID,
        source_version_id: UUID = SIXTEEN_TONS_SOURCE_VERSION_ID,
        requires_review: bool = False,
    ) -> None:
        async with self._music_uow() as uow:
            existing = await uow.lyrics_versions.get(version_id)
        if existing is None:
            await self._lyrics_versions.create(
                work_id,
                source_version_id,
                content,
                version_id=version_id,
            )
        elif (
            existing.language_tag != content.language_tag
            or existing.label != content.label
            or existing.body != content.body
            or existing.provenance != content.provenance
        ):
            await self._lyrics_versions.replace_content(version_id, content)
        async with self._music_uow() as uow:
            current = await uow.lyrics_versions.get(version_id)
        if current is not None and current.editorial_status is not GenreEditorialStatus.PUBLISHED:
            if requires_review:
                await self._lyrics_versions.submit_for_review(version_id)
            await self._lyrics_versions.publish(version_id)

    async def _ensure_lyrics_relations(self) -> None:
        await self._ensure_published_lyrics_relation(
            SIXTEEN_TONS_TRANSLATION_RELATION_ID,
            SIXTEEN_TONS_RU_READING_ID,
            SIXTEEN_TONS_EN_LYRICS_ID,
            SIXTEEN_TONS_TRANSLATION_RELATION,
        )
        await self._ensure_published_lyrics_relation(
            TRANSLATION_RELATION_ID,
            RUSSIAN_TRANSLATION_ID,
            ENGLISH_LYRICS_ID,
            TRANSLATION_RELATION,
        )

    async def _ensure_published_lyrics_relation(
        self,
        relation_id: UUID,
        source_version_id: UUID,
        target_version_id: UUID,
        content: LyricsVersionRelationContent,
    ) -> None:
        async with self._music_uow() as uow:
            existing = await uow.lyrics_version_relations.get(relation_id)
        if existing is None:
            await self._lyrics_relations.create(
                source_version_id,
                target_version_id,
                LyricsVersionRelationType.TRANSLATION_OF,
                content,
                relation_id=relation_id,
            )
        elif existing.provenance != content.provenance:
            await self._lyrics_relations.replace_content(relation_id, content)
        async with self._music_uow() as uow:
            current = await uow.lyrics_version_relations.get(relation_id)
        if current is not None and current.editorial_status is not GenreEditorialStatus.PUBLISHED:
            await self._lyrics_relations.publish(relation_id)

    async def _ensure_recordings(self) -> None:
        for recording_id, content in (*SEED_RECORDINGS, *PUBLIC_DOMAIN_RECORDINGS):
            async with self._music_uow() as uow:
                existing = await uow.recordings.get(recording_id)
            if existing is None:
                await self._recordings.create(content, recording_id=recording_id)
            elif (
                existing.title != content.title
                or existing.recorded_period != content.recorded_period
                or existing.description != content.description
                or existing.isrc != content.isrc
                or existing.credits != content.credits
                or existing.work_usages != content.work_usages
                or existing.lyrics_usages != content.lyrics_usages
            ):
                await self._replace_recording_content.execute(recording_id, content)
            async with self._music_uow() as uow:
                current = await uow.recordings.get(recording_id)
            if current is not None and current.editorial_status is not GenreEditorialStatus.PUBLISHED:
                await self._publish_recording.execute(recording_id)

    async def _ensure_recording_genre_assignments(self) -> None:
        for assignment_id, recording_id, genre_id, explanation in SEED_RECORDING_GENRE_ASSIGNMENTS:
            async with self._music_uow() as uow:
                existing = await uow.assignments.get(assignment_id)
                if existing is None:
                    assignment = ClassificationAssignment(
                        id=assignment_id,
                        target_kind=ClassificationTargetKind.RECORDING,
                        target_id=recording_id,
                        concept_id=genre_id,
                        explanation=explanation,
                        provenance=SEED_ASSIGNMENT_PROVENANCE,
                        evidence_status=MusicEvidenceStatus.UNVERIFIED,
                    ).publish()
                    await uow.assignments.add(assignment)
                else:
                    updated = existing.replace_content(
                        explanation=explanation,
                        claim_id=None,
                        provenance=SEED_ASSIGNMENT_PROVENANCE,
                        evidence_status=MusicEvidenceStatus.UNVERIFIED,
                    ).publish()
                    if updated != existing:
                        await uow.assignments.save(updated)
                await uow.commit()

    async def _ensure_recording_origin_claim(self) -> None:
        claim_id = MERLE_FIRST_RECORDING_CLAIM_ID
        async with self._hk_uow() as uow:
            existing = await uow.recording_origin_claims.get(claim_id)
        if existing is None:
            await self._create_recording_origin_claim.execute(
                MERLE_TRAVIS_RECORDING_ID,
                SIXTEEN_TONS_ID,
                MERLE_FIRST_RECORDING_PREDICATE,
                claim_id=claim_id,
            )
        await self._recording_origin_claims.replace_content(
            claim_id,
            explanation="Merle Travis recorded Sixteen Tons in 1946 before the later hit versions.",
            temporal=MERLE_FIRST_RECORDING_TEMPORAL,
            geographic=MERLE_FIRST_RECORDING_GEOGRAPHIC,
            provenance=MERLE_FIRST_RECORDING_PROVENANCE,
            evidence_status=EvidenceStatus.SUPPORTED,
        )
        await self._recording_origin_claims.replace_evidence(
            claim_id,
            MERLE_FIRST_RECORDING_EVIDENCE,
        )
        async with self._hk_uow() as uow:
            current = await uow.recording_origin_claims.get(claim_id)
        if current is not None and current.editorial_status is not ClaimEditorialStatus.PUBLISHED:
            await self._publish_recording_origin_claim.execute(claim_id)

    async def _ensure_listening_guide(self) -> None:
        guide_id = FORD_LISTENING_GUIDE_ID
        async with self._hk_uow() as uow:
            existing = await uow.listening_guides.get(guide_id)
        if existing is None:
            await self._listening_guides.create_draft(
                TENNESSEE_ERNIE_FORD_RECORDING_ID,
                FORD_LISTENING_GUIDE.observations,
                guide_id=guide_id,
            )
        elif existing.observations != FORD_LISTENING_GUIDE.observations:
            await self._replace_listening_guide_observations.execute(
                guide_id,
                FORD_LISTENING_GUIDE.observations,
            )
        async with self._hk_uow() as uow:
            current = await uow.listening_guides.get(guide_id)
        if current is not None and current.editorial_status is not ClaimEditorialStatus.PUBLISHED:
            await self._publish_listening_guide.execute(guide_id)
