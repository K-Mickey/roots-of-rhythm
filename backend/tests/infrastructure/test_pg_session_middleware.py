import asyncio
from typing import TYPE_CHECKING

from roots_of_rhythm.infrastructure.middlewares import PgSessionMiddleware
from tests.support.postgres import create_stub_accessor

if TYPE_CHECKING:
    from typing import Any


async def test_inherited_scope_is_reset_for_paths_outside_pg_prefixes() -> None:
    db = create_stub_accessor()
    executed: list[object] = []

    async def inner_app(scope: Any, receive: Any, send: Any) -> None:  # noqa: ARG001
        executed.append(await db.execute(object()))

    instance = PgSessionMiddleware(database=db, prefixes=("/api/v1",))
    app = instance(inner_app)
    asgi_scope: Any = {"type": "http", "path": "/api/v1/persons"}

    async def pipelined_request() -> None:
        await app(asgi_scope, None, None)  # type: ignore[arg-type]

    async with db.new_session():
        task = asyncio.create_task(pipelined_request())
    await task

    assert len(executed) == 1
