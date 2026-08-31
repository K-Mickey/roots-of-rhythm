from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock
from uuid import uuid7

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.infrastructure.transaction import SqlAlchemyTransactionScope
from roots_of_rhythm.music_catalog.domain import Recording, RecordingContent
from roots_of_rhythm.music_catalog.infrastructure.models import RecordingRecord
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository
from roots_of_rhythm.people_catalog.domain import Person, PersonContent
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord
from roots_of_rhythm.people_catalog.infrastructure.repository import SqlAlchemyPersonRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


@pytest.mark.asyncio
async def test_transaction_scope_rolls_back_failed_commit_and_closes_session() -> None:
    session = AsyncMock()
    session.commit.side_effect = RuntimeError("commit failed")
    scope = SqlAlchemyTransactionScope(cast("async_sessionmaker[AsyncSession]", lambda: session))

    with pytest.raises(RuntimeError, match="commit failed"):
        async with scope() as transaction:
            await transaction.commit()

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_transaction_scope_rolls_back_music_and_people_writes_together(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    recording = Recording.create(uuid7(), RecordingContent.create("Uncommitted recording"))
    person = Person.create(uuid7(), PersonContent.create("Uncommitted person"))
    scope = SqlAlchemyTransactionScope(session_factory)

    with pytest.raises(RuntimeError, match="abort transaction"):
        async with scope() as transaction:
            recordings = SqlAlchemyRecordingRepository(transaction.session)
            persons = SqlAlchemyPersonRepository(transaction.session)
            assert recordings._session is persons._session is transaction.session
            await recordings.add(recording)
            await persons.add(person)
            await transaction.session.flush()
            raise RuntimeError("abort transaction")

    async with session_factory() as session:
        assert await session.get(RecordingRecord, recording.id) is None
        assert await session.get(PersonRecord, person.id) is None
