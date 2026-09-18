"""Ordered entry point for the controlled corpus seed."""

from typing import TYPE_CHECKING

from roots_of_rhythm.seed.genre_knowledge import GenreKnowledgeSeed
from roots_of_rhythm.seed.musical_works import MusicalWorksSeed
from roots_of_rhythm.seed.people_and_groups import PeopleAndGroupsSeed
from roots_of_rhythm.seed.recording_corpus import RecordingCorpusSeed

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.application.ports import DbAccessor, UnitOfWork


class CorpusSeedRunner:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], database: DbAccessor, uow: UnitOfWork
    ) -> None:
        self._sections = (
            GenreKnowledgeSeed(session_factory),
            PeopleAndGroupsSeed(session_factory, database, uow),
            MusicalWorksSeed(session_factory),
            RecordingCorpusSeed(session_factory, database, uow),
        )

    async def run(self) -> None:
        for section in self._sections:
            await section.run()
