from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from roots_of_rhythm.historical_knowledge.domain import ListeningGuide, ListeningObservation
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
    updated = guide.replace_observations((second,))
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        await uow.listening_guides.save(updated)
        await uow.commit()
    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(factory) as uow:
        loaded = await uow.listening_guides.get_published_for_recording(guide.recording_id)
    assert loaded is not None
    assert [(item.id, item.position) for item in loaded.observations] == [(second.id, 1)]
