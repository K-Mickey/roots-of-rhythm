import logging
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency  # noqa: TC002 - Litestar inspects handler annotations at runtime
from litestar.params import FromPath  # noqa: TC002 - required at runtime for Litestar path binding
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto import (
    PerformerListResponse,  # noqa: TC001
    PerformerOverviewResponse,  # noqa: TC001
)
from roots_of_rhythm.discovery.application.errors import PerformerOverviewNotFound
from roots_of_rhythm.discovery.application.performer_list import (
    PerformerListReader,  # noqa: TC001
)
from roots_of_rhythm.discovery.application.performer_overview import (
    PerformerOverviewReader,  # noqa: TC001
)
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_performers_router() -> Router:
    @get()
    async def list_published_performers(
        performer_list_reader: NamedDependency[PerformerListReader],
    ) -> PerformerListResponse | Response[ErrorResponse]:
        try:
            return await performer_list_reader.list()
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to list published Performers", extra={"request_id": request_id})
            return _error_response(500, "INTERNAL_ERROR", _INTERNAL_ERROR_MESSAGE, request_id=request_id)

    @get("/{performer_id:str}")
    async def get_published_performer_overview(
        performer_id: FromPath[str],
        performer_overview_reader: NamedDependency[PerformerOverviewReader],
    ) -> PerformerOverviewResponse | Response[ErrorResponse]:
        try:
            parsed_id = UUID(performer_id)
        except ValueError:
            return _error_response(404, "PERFORMER_NOT_FOUND", _NOT_FOUND_MESSAGE)
        try:
            return await performer_overview_reader.get(parsed_id)
        except PerformerOverviewNotFound:
            return _error_response(404, "PERFORMER_NOT_FOUND", _NOT_FOUND_MESSAGE)
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Performer overview", extra={"request_id": request_id})
            return _error_response(500, "INTERNAL_ERROR", _INTERNAL_ERROR_MESSAGE, request_id=request_id)

    return Router(
        path="/api/v1/performers",
        route_handlers=[list_published_performers, get_published_performer_overview],
    )


def _error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    request_id: str | None = None,
) -> Response[ErrorResponse]:
    return Response(
        ErrorResponse(code=code, message=message, details=None, request_id=request_id or str(uuid7())),
        status_code=status_code,
    )
