from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy import func, select

from roots_of_rhythm.historical_knowledge.application import UniqueConstraintViolation
from roots_of_rhythm.historical_knowledge.domain import ListeningGuide, ListeningObservation
from roots_of_rhythm.historical_knowledge.infrastructure.models import ListeningObservationRecord
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.infrastructure.database import create_session_factory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_listening_guide_round_trip_and_soft_replace(engine: AsyncEngine) -> None:
    factory = create_session_factory(engine)
    first = ListeningObservation.create("Theme", "Notice the theme.", uuid7(), datetime.now(UTC))
    second = ListeningObservation.create("Solo", "Notice the solo.", uuid7(), datetime.now(UTC))
    guide = ListeningGuide.create_draft(uuid7(), (first, second)).publish()
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        await uow.listening_guides.add(guide)
        await uow.commit()
    updated = guide.replace_observations((second, first))
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        await uow.listening_guides.save(updated)
        await uow.commit()
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        loaded = await uow.listening_guides.get_published_for_recording(guide.recording_id)
    assert loaded is not None
    assert [(item.id, item.position) for item in loaded.observations] == [(second.id, 1), (first.id, 2)]

    replacement = ListeningObservation.create("Ending", "Notice the ending.", uuid7(), datetime.now(UTC))
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        await uow.listening_guides.save(updated.replace_observations((replacement,)))
        await uow.commit()
    async with factory() as session:
        rows = list(
            await session.scalars(
                select(ListeningObservationRecord).where(ListeningObservationRecord.guide_id == guide.id)
            )
        )
    assert {(row.id, row.deleted) for row in rows} == {
        (first.id, True),
        (second.id, True),
        (replacement.id, False),
    }

    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        await uow.listening_guides.save(updated.replace_observations((first,)))
        await uow.commit()
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        revived = await uow.listening_guides.get(guide.id)
    assert revived is not None
    assert [(item.id, item.position) for item in revived.observations] == [(first.id, 1)]


@pytest.mark.asyncio
async def test_listening_guide_translates_active_recording_conflict(engine: AsyncEngine) -> None:
    factory = create_session_factory(engine)
    recording_id = uuid7()
    first = ListeningGuide.create_draft(recording_id)
    second = ListeningGuide.create_draft(recording_id)

    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        await uow.listening_guides.add(first)
        await uow.commit()
    with pytest.raises(UniqueConstraintViolation):
        async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
            await uow.listening_guides.add(second)

    async with factory() as session:
        count = await session.scalar(select(func.count()).select_from(ListeningObservationRecord))
    assert count == 0
