"""Seeded corpus fixture for public Genre HTTP integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.seed import CorpusSeedRunner

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture
async def seeded_engine(engine: AsyncEngine) -> AsyncEngine:
    await CorpusSeedRunner(create_session_factory(engine)).run()
    return engine
