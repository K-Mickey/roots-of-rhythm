from unittest.mock import patch

import pytest

from roots_of_rhythm.infrastructure.base import PgConfig
from roots_of_rhythm.infrastructure.pg_accessor import PgAccessor
from roots_of_rhythm.infrastructure.uow import PgUnitOfWork


@pytest.mark.asyncio
async def test_uow_reuses_existing_session() -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    uow = PgUnitOfWork(pg)
    fake_session = object()

    with (
        patch.object(pg, "in_child_task", return_value=False),
        patch.object(pg, "get_current_session", return_value=fake_session),
        patch.object(pg, "new_session") as mock_new_session,
    ):
        async with uow():
            assert pg.get_current_session() is fake_session
        mock_new_session.assert_not_called()


@pytest.mark.asyncio
async def test_uow_from_child_task_raises_without_touching_session() -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    uow = PgUnitOfWork(pg)

    with (
        patch.object(pg, "in_child_task", return_value=True),
        patch.object(pg, "get_current_session") as mock_get_current_session,
        patch.object(pg, "new_session") as mock_new_session,
    ):
        with pytest.raises(RuntimeError, match="child task"):
            async with uow():
                pass
        # Порядок гардов принципиален: get_current_session() — peek, он не
        # материализует child-сессию, но при перестановке проверок вместо этого
        # сообщения полетел бы другой RuntimeError из new_session().
        mock_get_current_session.assert_not_called()
        mock_new_session.assert_not_called()


@pytest.mark.asyncio
async def test_uow_opens_new_session_when_no_active_scope() -> None:
    pg = PgAccessor(PgConfig(database="stub"))
    uow = PgUnitOfWork(pg)

    with (
        patch.object(pg, "in_child_task", return_value=False),
        patch.object(pg, "get_current_session", return_value=None),
        patch.object(pg, "new_session") as mock_new_session,
    ):
        async with uow():
            pass

    mock_new_session.assert_called_once()
