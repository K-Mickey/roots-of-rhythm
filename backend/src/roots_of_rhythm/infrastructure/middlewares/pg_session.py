from typing import TYPE_CHECKING

from litestar.enums import ScopeType
from litestar.middleware import ASGIMiddleware

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send

    from roots_of_rhythm.application.ports import DbAccessor


class PgSessionMiddleware(ASGIMiddleware):
    scopes = (ScopeType.HTTP,)

    def __init__(self, database: DbAccessor, prefixes: tuple[str, ...]) -> None:
        self._db = database
        self._prefixes = prefixes

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        self._db.reset_request_scope()

        path: str = scope.get("path", "")
        if not path.startswith(self._prefixes):
            await next_app(scope, receive, send)
            return

        async with self._db.new_session():
            await next_app(scope, receive, send)
