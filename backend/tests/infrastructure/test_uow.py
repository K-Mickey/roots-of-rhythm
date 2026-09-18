from unittest.mock import patch

import pytest

from roots_of_rhythm.infrastructure.uow import PgUnitOfWork
from tests.support.postgres import create_stub_accessor


@pytest.mark.asyncio
async def test_uow_reuses_existing_session() -> None:
    db = create_stub_accessor()
    uow = PgUnitOfWork(db)
    fake_session = object()

    with (
        patch.object(db, "in_child_task", return_value=False),
        patch.object(db, "get_current_session", return_value=fake_session),
        patch.object(db, "new_session") as mock_new_session,
    ):
        async with uow():
            assert db.get_current_session() is fake_session
        mock_new_session.assert_not_called()


@pytest.mark.asyncio
async def test_uow_from_child_task_raises_without_touching_session() -> None:
    db = create_stub_accessor()
    uow = PgUnitOfWork(db)

    with (
        patch.object(db, "in_child_task", return_value=True),
        patch.object(db, "get_current_session") as mock_get_current_session,
        patch.object(db, "new_session") as mock_new_session,
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
    db = create_stub_accessor()
    uow = PgUnitOfWork(db)

    with (
        patch.object(db, "in_child_task", return_value=False),
        patch.object(db, "get_current_session", return_value=None),
        patch.object(db, "new_session") as mock_new_session,
    ):
        async with uow():
            pass

    mock_new_session.assert_called_once()
