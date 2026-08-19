import logging
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency  # noqa: TC002 - Litestar inspects handler annotations at runtime
from litestar.params import FromPath  # noqa: TC002 - required at runtime for Litestar path binding
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto import (
    GenreListResponse,  # noqa: TC001 - Litestar inspects handler annotations at runtime
    GenreOverviewResponse,  # noqa: TC001 - Litestar inspects handler annotations at runtime
    GenreRelationsResponse,  # noqa: TC001 - Litestar inspects handler annotations at runtime
    GenreSourcesResponse,  # noqa: TC001 - Litestar inspects handler annotations at runtime
)
from roots_of_rhythm.discovery.application.errors import (
    GenreOverviewNotFound,
    GenreRelationsNotFound,
    GenreSourcesNotFound,
)
from roots_of_rhythm.discovery.application.genre_list import (
    GenreListReader,  # noqa: TC001 - Litestar inspects handler annotations at runtime
)
from roots_of_rhythm.discovery.application.genre_overview import (
    GenreOverviewReader,  # noqa: TC001 - Litestar inspects handler annotations at runtime
)
from roots_of_rhythm.discovery.application.genre_relations import (
    GenreRelationsReader,  # noqa: TC001 - Litestar inspects handler annotations at runtime
)
from roots_of_rhythm.discovery.application.genre_sources import (
    GenreSourcesReader,  # noqa: TC001 - Litestar inspects handler annotations at runtime
)
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_GENRE_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_genres_router() -> Router:
    @get()
    async def list_published_genres(
        genre_list_reader: NamedDependency[GenreListReader],
    ) -> GenreListResponse | Response[ErrorResponse]:
        try:
            return await genre_list_reader.list()
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to list published Genres", extra={"request_id": request_id})
            return _error_response(
                500,
                "INTERNAL_ERROR",
                _INTERNAL_ERROR_MESSAGE,
                request_id=request_id,
            )

    @get("/{genre_id:str}")
    async def get_published_genre_overview(
        genre_id: FromPath[str],
        genre_overview_reader: NamedDependency[GenreOverviewReader],
    ) -> GenreOverviewResponse | Response[ErrorResponse]:
        try:
            parsed_id = UUID(genre_id)
        except ValueError:
            return _error_response(404, "GENRE_NOT_FOUND", _GENRE_NOT_FOUND_MESSAGE)
        try:
            return await genre_overview_reader.get(parsed_id)
        except GenreOverviewNotFound:
            return _error_response(404, "GENRE_NOT_FOUND", _GENRE_NOT_FOUND_MESSAGE)
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Genre overview", extra={"request_id": request_id})
            return _error_response(
                500,
                "INTERNAL_ERROR",
                _INTERNAL_ERROR_MESSAGE,
                request_id=request_id,
            )

    @get("/{genre_id:str}/relations")
    async def get_published_genre_relations(
        genre_id: FromPath[str],
        genre_relations_reader: NamedDependency[GenreRelationsReader],
    ) -> GenreRelationsResponse | Response[ErrorResponse]:
        try:
            parsed_id = UUID(genre_id)
        except ValueError:
            return _error_response(404, "GENRE_NOT_FOUND", _GENRE_NOT_FOUND_MESSAGE)
        try:
            return await genre_relations_reader.get(parsed_id)
        except GenreRelationsNotFound:
            return _error_response(404, "GENRE_NOT_FOUND", _GENRE_NOT_FOUND_MESSAGE)
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Genre relations", extra={"request_id": request_id})
            return _error_response(
                500,
                "INTERNAL_ERROR",
                _INTERNAL_ERROR_MESSAGE,
                request_id=request_id,
            )

    @get("/{genre_id:str}/sources")
    async def get_published_genre_sources(
        genre_id: FromPath[str],
        genre_sources_reader: NamedDependency[GenreSourcesReader],
    ) -> GenreSourcesResponse | Response[ErrorResponse]:
        try:
            parsed_id = UUID(genre_id)
        except ValueError:
            return _error_response(404, "GENRE_NOT_FOUND", _GENRE_NOT_FOUND_MESSAGE)
        try:
            return await genre_sources_reader.get(parsed_id)
        except GenreSourcesNotFound:
            return _error_response(404, "GENRE_NOT_FOUND", _GENRE_NOT_FOUND_MESSAGE)
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Genre sources", extra={"request_id": request_id})
            return _error_response(
                500,
                "INTERNAL_ERROR",
                _INTERNAL_ERROR_MESSAGE,
                request_id=request_id,
            )

    return Router(
        path="/api/v1/genres",
        route_handlers=[
            list_published_genres,
            get_published_genre_overview,
            get_published_genre_relations,
            get_published_genre_sources,
        ],
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
