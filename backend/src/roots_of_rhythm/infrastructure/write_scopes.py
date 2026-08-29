from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import SqlAlchemyHistoricalKnowledgeUnitOfWork
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from roots_of_rhythm.music_catalog.application.ports import RecordingUnitOfWork


@asynccontextmanager
async def music_people_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[tuple[SqlAlchemyMusicCatalogUnitOfWork, SqlAlchemyPeopleCatalogUnitOfWork]]:
    session = session_factory()
    try:
        yield (
            SqlAlchemyMusicCatalogUnitOfWork.using(session),
            SqlAlchemyPeopleCatalogUnitOfWork.using(session),
        )
    except BaseException:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def knowledge_music_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[tuple[SqlAlchemyHistoricalKnowledgeUnitOfWork, RecordingUnitOfWork]]:
    session = session_factory()
    try:
        music_uow: RecordingUnitOfWork = SqlAlchemyMusicCatalogUnitOfWork.using(session)
        yield (
            SqlAlchemyHistoricalKnowledgeUnitOfWork.using(session),
            music_uow,
        )
    except BaseException:
        await session.rollback()
        raise
    finally:
        await session.close()
