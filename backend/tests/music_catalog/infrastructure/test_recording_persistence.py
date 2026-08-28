from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy import select

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.infrastructure.write_scopes import music_people_scope
from roots_of_rhythm.music_catalog.application import GroupService, MusicalWorkService, RecordingService
from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
    ExistencePeriod,
    GroupContent,
    RecordingContent,
    RecordingContributionKind,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
    TemporalBound,
    TemporalPrecision,
    WorkContent,
)
from roots_of_rhythm.music_catalog.infrastructure.models import RecordingCreditRecord, RecordingWorkUsageRecord
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.application import PersonService
from roots_of_rhythm.people_catalog.domain import PersonContent
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_recording_round_trip_replace_lifecycle_and_soft_delete(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    works = MusicalWorkService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    recordings = RecordingService(lambda: music_people_scope(session_factory))
    persons = PersonService(lambda: SqlAlchemyPeopleCatalogUnitOfWork(session_factory))
    groups = GroupService(lambda: SqlAlchemyMusicCatalogUnitOfWork(session_factory))
    work = await works.create(WorkContent.create("Sixteen Tons", provenance="Editorial note"))
    await works.publish(work.id)
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
        )
    )
    async with session_factory() as session:
        credit_created_at = await session.scalar(
            select(RecordingCreditRecord.created_at).where(RecordingCreditRecord.id == primary.id)
        )
    published = await recordings.publish(created.id)

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
    replaced = await recordings.replace_content(
        created.id,
        RecordingContent.create(
            "Sixteen Tons — excerpt",
            recording_credits=(replacement_credit,),
            work_usages=(replacement_usage,),
        ),
    )
    assert replaced.editorial_status is EditorialStatus.PUBLISHED
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get(created.id) == replaced
    async with session_factory() as session:
        assert (
            await session.scalar(select(RecordingCreditRecord.deleted).where(RecordingCreditRecord.id == primary.id))
            is True
        )
        assert (
            await session.scalar(
                select(RecordingWorkUsageRecord.deleted).where(RecordingWorkUsageRecord.id == usage.id)
            )
            is True
        )

    restored = await recordings.replace_content(
        created.id,
        RecordingContent.create(
            "Sixteen Tons — restored",
            recording_credits=(primary,),
            work_usages=(usage,),
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
    recordings = RecordingService(lambda: music_people_scope(session_factory))
    draft = await recordings.create(RecordingContent.create("Draft"))

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assert await uow.recordings.get_published(draft.id) is None
