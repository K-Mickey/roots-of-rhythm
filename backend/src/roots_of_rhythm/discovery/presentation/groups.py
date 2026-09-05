import logging
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency  # noqa: TC002 - Litestar inspects handler annotations at runtime
from litestar.params import FromPath  # noqa: TC002 - required at runtime for Litestar path binding
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto.groups import (
    GroupListResponse,  # noqa: TC001
    GroupOverviewResponse,  # noqa: TC001
)  # noqa: TC001 - Litestar resolves handler annotations at runtime
from roots_of_rhythm.discovery.application.errors.groups import GroupOverviewNotFound
from roots_of_rhythm.discovery.application.queries.group_list import (
    GroupListReader,  # noqa: TC001
)
from roots_of_rhythm.discovery.application.queries.group_overview import (
    GroupOverviewReader,  # noqa: TC001
)
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_groups_router() -> Router:
    @get()
    async def list_published_groups(
        group_list_reader: NamedDependency[GroupListReader],
    ) -> GroupListResponse | Response[ErrorResponse]:
        try:
            return await group_list_reader.list()
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to list published Groups", extra={"request_id": request_id})
            return _error_response(500, "INTERNAL_ERROR", _INTERNAL_ERROR_MESSAGE, request_id=request_id)

    @get("/{group_id:str}")
    async def get_published_group_overview(
        group_id: FromPath[str],
        group_overview_reader: NamedDependency[GroupOverviewReader],
    ) -> GroupOverviewResponse | Response[ErrorResponse]:
        try:
            parsed_id = UUID(group_id)
        except ValueError:
            return _error_response(404, "GROUP_NOT_FOUND", _NOT_FOUND_MESSAGE)
        try:
            return await group_overview_reader.get(parsed_id)
        except GroupOverviewNotFound:
            return _error_response(404, "GROUP_NOT_FOUND", _NOT_FOUND_MESSAGE)
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Group overview", extra={"request_id": request_id})
            return _error_response(500, "INTERNAL_ERROR", _INTERNAL_ERROR_MESSAGE, request_id=request_id)

    return Router(
        path="/api/v1/groups",
        route_handlers=[list_published_groups, get_published_group_overview],
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
