from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy import select

from roots_of_rhythm.historical_knowledge.domain import Source, SourceVersion
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope, sqlalchemy_session
from roots_of_rhythm.music_catalog.application import (
    GroupService,
    LyricsVersionService,
    MusicalWorkService,
    PublishRecording,
    RecordingService,
    ReplaceRecordingContent,
)
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    ExistencePeriod,
    GroupContent,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionContent,
    RecordingContent,
    RecordingContributionKind,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingLyricsUsage,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
)
from roots_of_rhythm.music_catalog.infrastructure.group_repository import SqlAlchemyGroupRepository
from roots_of_rhythm.music_catalog.infrastructure.lyrics_version_repository import SqlAlchemyLyricsVersionRepository
from roots_of_rhythm.music_catalog.infrastructure.models import (
    RecordingCreditRecord,
    RecordingLyricsUsageRecord,
    RecordingWorkUsageRecord,
)
from roots_of_rhythm.music_catalog.infrastructure.musical_work_repository import SqlAlchemyMusicalWorkRepository
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import PersonContent
from roots_of_rhythm.people_catalog.infrastructure.repository import SqlAlchemyPersonRepository
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

    from roots_of_rhythm.application.transaction import Transaction

pytestmark = pytest.mark.integration


def _recording_operations(
    session_factory: "async_sessionmaker[AsyncSession]",
) -> tuple[RecordingService, PublishRecording, ReplaceRecordingContent]:
    transaction_scope = SqlAlchemyTransactionScope(session_factory)

    def recording_repository(transaction: "Transaction") -> SqlAlchemyRecordingRepository:
        return SqlAlchemyRecordingRepository(sqlalchemy_session(transaction))

    service = RecordingService(transaction_scope, recording_repository)
    publish = PublishRecording(
        transaction_scope,
        recording_repository,
        lambda transaction: SqlAlchemyMusicalWorkRepository(sqlalchemy_session(transaction)),
        lambda transaction: SqlAlchemyLyricsVersionRepository(sqlalchemy_session(transaction)),
        lambda transaction: SqlAlchemyGroupRepository(sqlalchemy_session(transaction)),
        lambda transaction: SqlAlchemyPersonRepository(sqlalchemy_session(transaction)),
    )
    replace = ReplaceRecordingContent(
        transaction_scope,
        recording_repository,
        lambda transaction: SqlAlchemyMusicalWorkRepository(sqlalchemy_session(transaction)),
        lambda transaction: SqlAlchemyLyricsVersionRepository(sqlalchemy_session(transaction)),
        lambda transaction: SqlAlchemyGroupRepository(sqlalchemy_session(transaction)),
        lambda transaction: SqlAlchemyPersonRepository(sqlalchemy_session(transaction)),
    )
    return service, publish, replace


@pytest.mark.asyncio
async def test_recording_round_trip_replace_lifecycle_and_soft_delete(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    works = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    lyrics = LyricsVersionService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    recordings, publish_recording, replace_recording_content = _recording_operations(session_factory)
    persons = PersonService(lambda: SqlAlchemyPeopleCatalogUnitOfWork(session_factory))
    groups = GroupService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    work = await works.create(WorkContent.create("Sixteen Tons", provenance="Editorial note"))
    await works.publish(work.id)
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory) as hk:
        source = Source.create("Lyrics source")
        source_version = SourceVersion.create(source.id, "v1")
        await hk.sources.add_source(source)
        await hk.sources.add_version(source_version)
        await hk.commit()
    lyrics_version = await lyrics.create(
        work.id,
        source_version.id,
        LyricsVersionContent.create(
            language_tag="en",
            usage_kind=LyricsUsageKind.PERFORMABLE,
            creation_method=LyricsCreationMethod.ORIGINAL,
        ),
    )
    await lyrics.publish(lyrics_version.id)
    person = await persons.create(PersonContent.create("Tennessee Ernie Ford"))
    await persons.publish(person.id)
    group = await groups.create(GroupContent.create("Studio group"))
    await groups.publish(group.id)
    primary = RecordingCredit.create(
        uuid7(),
        RecordingCreditTargetKind.PERSON,
        person.id,
        BillingRole.PRIMARY,
        contribution_kind=RecordingContributionKind.VOCAL,
        credited_as="Tennessee Ernie Ford",
    )
    additional = RecordingCredit.create(uuid7(), RecordingCreditTargetKind.GROUP, uuid7(), BillingRole.ADDITIONAL)
    usage = RecordingWorkUsage.create(uuid7(), work.id, RecordingWorkUsageKind.COMPLETE)
    lyrics_usage = RecordingLyricsUsage.create(uuid7(), lyrics_version.id)
    period = ExistencePeriod.create(
        TemporalBound(1955, TemporalPrecision.EXACT_YEAR),
        TemporalBound(1955, TemporalPrecision.EXACT_YEAR),
    )
    created = await recordings.create(
        RecordingContent.create(
            "Sixteen Tons",
            recorded_period=period,
            description="Studio recording.",
            isrc="US-AAA-55-00001",
            recording_credits=(primary, additional),
            work_usages=(usage,),
            lyrics_usages=(lyrics_usage,),
        )
    )
    async with session_factory() as session:
        credit_created_at = await session.scalar(
            select(RecordingCreditRecord.created_at).where(RecordingCreditRecord.id == primary.id)
        )
    published = await publish_recording.execute(created.id)

    async with session_factory() as session:
        assert (
            await session.scalar(select(RecordingCreditRecord.created_at).where(RecordingCreditRecord.id == primary.id))
            == credit_created_at
        )

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        loaded = await uow.recordings.get_published(created.id)
    assert loaded == published
    assert loaded is not None
    assert loaded.recorded_period == period
    assert loaded.isrc == "USAAA5500001"
    assert len(loaded.credits) == 2

    replacement_credit = RecordingCredit.create(uuid7(), RecordingCreditTargetKind.GROUP, group.id, BillingRole.PRIMARY)
    replacement_usage = RecordingWorkUsage.create(uuid7(), work.id, RecordingWorkUsageKind.COMPLETE)
    replaced = await replace_recording_content.execute(
        created.id,
        RecordingContent.create(
            "Sixteen Tons — excerpt",
            recording_credits=(replacement_credit,),
            work_usages=(replacement_usage,),
        ),
    )
    assert replaced.is_published
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get(created.id) == replaced
    async with session_factory() as session:
        assert (
            await session.scalar(select(RecordingCreditRecord.deleted).where(RecordingCreditRecord.id == primary.id))
            is True
        )
        assert (
            await session.scalar(
                select(RecordingLyricsUsageRecord.deleted).where(RecordingLyricsUsageRecord.id == lyrics_usage.id)
            )
            is True
        )
        assert (
            await session.scalar(
                select(RecordingWorkUsageRecord.deleted).where(RecordingWorkUsageRecord.id == usage.id)
            )
            is True
        )

    restored = await replace_recording_content.execute(
        created.id,
        RecordingContent.create(
            "Sixteen Tons — restored",
            recording_credits=(primary,),
            work_usages=(usage,),
            lyrics_usages=(lyrics_usage,),
        ),
    )
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get(created.id) == restored
    async with session_factory() as session:
        assert (
            await session.scalar(select(RecordingCreditRecord.deleted).where(RecordingCreditRecord.id == primary.id))
            is False
        )
        assert (
            await session.scalar(
                select(RecordingLyricsUsageRecord.deleted).where(RecordingLyricsUsageRecord.id == lyrics_usage.id)
            )
            is False
        )
        assert (
            await session.scalar(
                select(RecordingWorkUsageRecord.deleted).where(RecordingWorkUsageRecord.id == usage.id)
            )
            is False
        )

    await recordings.archive(created.id)
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get_published(created.id) is None
        await uow.recordings.mark_deleted(created.id)
        await uow.commit()
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get(created.id) is None


@pytest.mark.asyncio
async def test_draft_recording_is_not_returned_as_published(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    recordings, _publish_recording, _replace_recording_content = _recording_operations(session_factory)
    draft = await recordings.create(RecordingContent.create("Draft"))

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get_published(draft.id) is None
