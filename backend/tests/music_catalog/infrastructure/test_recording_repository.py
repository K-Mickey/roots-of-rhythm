from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid7

import pytest
from psycopg.errors import Diagnostic, UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from roots_of_rhythm.music_catalog.application import UniqueConstraintViolation
from roots_of_rhythm.music_catalog.domain import Recording, RecordingContent, RecordingWorkUsage, RecordingWorkUsageKind
from roots_of_rhythm.music_catalog.infrastructure.models import RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT
from roots_of_rhythm.music_catalog.infrastructure.recording_repository import SqlAlchemyRecordingRepository


class _RecordingUniqueViolation(UniqueViolation):
    @property
    def diag(self) -> Diagnostic:
        return cast("Diagnostic", SimpleNamespace(constraint_name=RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT))


@pytest.mark.asyncio
async def test_recording_repository_translates_owned_unique_constraint() -> None:
    session = MagicMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.flush.side_effect = [None, IntegrityError(None, None, _RecordingUniqueViolation())]
    repository = SqlAlchemyRecordingRepository(cast("AsyncSession", session))
    recording = Recording.create(
        uuid7(),
        RecordingContent.create(
            "Recording",
            work_usages=(RecordingWorkUsage.create(uuid7(), uuid7(), RecordingWorkUsageKind.COMPLETE),),
        ),
    )

    with pytest.raises(UniqueConstraintViolation) as error:
        await repository.add(recording)

    assert error.value.constraint_name == RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT
