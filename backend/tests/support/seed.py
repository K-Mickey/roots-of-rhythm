from __future__ import annotations

from typing import TYPE_CHECKING

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.seed import CorpusSeedRunner

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    from roots_of_rhythm.application.ports import DbAccessor, UnitOfWork


async def run_corpus_seed(engine: AsyncEngine, database: DbAccessor, uow: UnitOfWork) -> None:
    corpus = CorpusSeedRunner(
        session_factory=create_session_factory(engine),
        database=database,
        uow=uow,
    )
    await corpus.run()
