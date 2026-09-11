import asyncio
import logging
from typing import TYPE_CHECKING

from roots_of_rhythm.infrastructure.base import CHILD_CANCEL_GRACE_SECONDS, PG_RO_CHILD_INFO_KEY

if TYPE_CHECKING:
    from typing import Any

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class SessionScope:
    __slots__ = (
        "_children",
        "_cleanup_tasks",
        "_closed",
        "_main_has_writes",
        "_main_session",
        "_main_task",
        "_ro_session_maker",
        "_warn_threshold",
        "_warned_many_children",
        "_warned_read_after_write",
    )

    def __init__(
        self,
        *,
        main_task: "asyncio.Task[Any] | None",
        main_session: AsyncSession,
        ro_session_maker: async_sessionmaker[AsyncSession],
        warn_threshold: int,
    ) -> None:
        self._main_task = main_task
        self._main_session = main_session
        self._ro_session_maker = ro_session_maker
        self._warn_threshold = warn_threshold
        self._children: dict[asyncio.Task[Any], AsyncSession] = {}
        self._cleanup_tasks: set[asyncio.Task[None]] = set()
        self._closed = False
        self._main_has_writes = False
        self._warned_many_children = False
        self._warned_read_after_write = False

    def get(self) -> AsyncSession:
        task = asyncio.current_task()
        if task is None or task is self._main_task:
            return self._main_session
        if self._closed:
            raise RuntimeError("pg session scope is already closed")
        session = self._children.get(task)
        if session is not None:
            return session

        session = self._ro_session_maker()
        self._children[task] = session
        task.add_done_callback(self._on_child_done)
        if self._main_has_writes and not self._warned_read_after_write:
            self._warned_read_after_write = True
            logger.warning(
                "pg session scope: read-only child session created after main-session writes; "
                "child will not see uncommitted changes (task=%r)",
                task.get_name(),
            )
        if not self._warned_many_children and len(self._children) > self._warn_threshold:
            self._warned_many_children = True
            logger.warning("pg session scope: %d concurrent child sessions", len(self._children))
        return session

    def peek(self) -> "AsyncSession | None":
        task = asyncio.current_task()
        if task is None or task is self._main_task:
            return self._main_session
        return self._children.get(task)

    def is_child_task(self) -> bool:
        task = asyncio.current_task()
        return task is not None and task is not self._main_task

    def on_dml(self, session: AsyncSession) -> None:
        if session is self._main_session:
            self._main_has_writes = True
            return
        if session.info.get(PG_RO_CHILD_INFO_KEY):
            raise RuntimeError(
                "DML on a read-only child pg session: writes must run in the main task of the "
                "request scope (do not write to pg inside asyncio.gather branches)"
            )

    def reject_cross_task_session(self, session: AsyncSession) -> None:
        current_task = asyncio.current_task()
        if session is self._main_session:
            owner_task = self._main_task
        else:
            owner_task = next(
                (task for task, child_session in self._children.items() if child_session is session),
                None,
            )
        if owner_task is not None and owner_task is not current_task:
            raise RuntimeError(
                "explicit pg session used from a task that does not own it: reads and writes must "
                "run in the task the session belongs to (do not pass the main or a child session "
                "into other asyncio.gather branches)"
            )

    def _on_child_done(self, task: "asyncio.Task[Any]") -> None:
        session = self._children.pop(task, None)
        if session is None:
            return
        try:
            cleanup = asyncio.get_running_loop().create_task(self._close_session(session))
        except RuntimeError:
            logger.warning("pg session scope: no running loop to close child session")
            return
        self._cleanup_tasks.add(cleanup)
        cleanup.add_done_callback(self._cleanup_tasks.discard)

    @staticmethod
    async def _close_session(session: AsyncSession) -> None:
        try:
            await session.close()
        except Exception:
            logger.exception("failed to close child pg session")

    async def close_children(self) -> None:
        self._closed = True
        cancelled = False
        stragglers = [t for t in self._children if not t.done()]
        for t in stragglers:
            t.cancel()
        if stragglers:
            try:
                await asyncio.wait(stragglers, timeout=CHILD_CANCEL_GRACE_SECONDS)
            except asyncio.CancelledError:
                cancelled = True
        for task in list(self._children):
            if not task.done():
                logger.error(
                    "pg session scope: child task %r survived cancellation; "
                    "its session will be closed by the task's done-callback",
                    task.get_name(),
                )
                continue
            session = self._children.pop(task, None)
            if session is None:
                continue
            try:
                await self._close_session(session)
            except asyncio.CancelledError:
                cancelled = True
        if self._cleanup_tasks:
            try:
                await asyncio.gather(*list(self._cleanup_tasks), return_exceptions=True)
            except asyncio.CancelledError:
                cancelled = True
        if cancelled:
            raise asyncio.CancelledError
