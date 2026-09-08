import logging
from http import HTTPStatus
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
from roots_of_rhythm.discovery.application.queries.group_list import GroupListReader  # noqa: TC001
from roots_of_rhythm.discovery.application.queries.group_overview import GroupOverviewReader  # noqa: TC001
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_groups_router() -> Router:
    return Router(
        path="/api/v1/groups",
        route_handlers=[
            list_published_groups,
            get_published_group_overview,
        ],
    )


@get()
async def list_published_groups(
    group_list_reader: NamedDependency[GroupListReader],
) -> GroupListResponse | Response[ErrorResponse]:
    try:
        return await group_list_reader.list()
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to list published Groups", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message=_INTERNAL_ERROR_MESSAGE,
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@get("/{group_id:str}")
async def get_published_group_overview(
    group_id: FromPath[str],
    group_overview_reader: NamedDependency[GroupOverviewReader],
) -> GroupOverviewResponse | Response[ErrorResponse]:
    try:
        parsed_id = UUID(group_id)
    except ValueError:
        return Response(
            ErrorResponse(
                code="GROUP_NOT_FOUND",
                message=_NOT_FOUND_MESSAGE,
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    try:
        return await group_overview_reader.get(parsed_id)
    except GroupOverviewNotFound:
        return Response(
            ErrorResponse(
                code="GROUP_NOT_FOUND",
                message=_NOT_FOUND_MESSAGE,
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to assemble Group overview", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message=_INTERNAL_ERROR_MESSAGE,
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
