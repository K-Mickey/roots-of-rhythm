import logging
from http import HTTPStatus
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency  # noqa: TC002 - Litestar inspects handler annotations at runtime
from litestar.params import FromPath  # noqa: TC002 - required at runtime for Litestar path binding
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto.performers import (
    PerformerListResponse,  # noqa: TC001
    PerformerOverviewResponse,  # noqa: TC001
)  # noqa: TC001 - Litestar resolves handler annotations at runtime
from roots_of_rhythm.discovery.application.errors.performers import PerformerOverviewNotFound
from roots_of_rhythm.discovery.application.queries.performer_list import PerformerListReader  # noqa: TC001
from roots_of_rhythm.discovery.application.queries.performer_overview import PerformerOverviewReader  # noqa: TC001
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_performers_router() -> Router:
    return Router(
        path="/api/v1/performers",
        route_handlers=[
            list_published_performers,
            get_published_performer_overview,
        ],
    )


@get()
async def list_published_performers(
    performer_list_reader: NamedDependency[PerformerListReader],
) -> PerformerListResponse | Response[ErrorResponse]:
    try:
        return await performer_list_reader.list()
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to list published Performers", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message=_INTERNAL_ERROR_MESSAGE,
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@get("/{performer_id:str}")
async def get_published_performer_overview(
    performer_id: FromPath[str],
    performer_overview_reader: NamedDependency[PerformerOverviewReader],
) -> PerformerOverviewResponse | Response[ErrorResponse]:
    try:
        parsed_id = UUID(performer_id)
    except ValueError:
        return Response(
            ErrorResponse(
                code="PERFORMER_NOT_FOUND",
                message=_NOT_FOUND_MESSAGE,
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    try:
        return await performer_overview_reader.get(parsed_id)
    except PerformerOverviewNotFound:
        return Response(
            ErrorResponse(
                code="PERFORMER_NOT_FOUND",
                message=_NOT_FOUND_MESSAGE,
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to assemble Performer overview", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message=_INTERNAL_ERROR_MESSAGE,
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
