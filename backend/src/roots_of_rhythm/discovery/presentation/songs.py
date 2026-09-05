import logging
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency  # noqa: TC002 - Litestar inspects handler annotations at runtime
from litestar.params import FromPath  # noqa: TC002 - required at runtime for Litestar path binding
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto.songs import (
    SongListResponse,  # noqa: TC001
    SongOverviewResponse,  # noqa: TC001
)  # noqa: TC001 - Litestar resolves handler annotations at runtime
from roots_of_rhythm.discovery.application.errors.songs import SongOverviewNotFound
from roots_of_rhythm.discovery.application.queries.song_list import SongListReader  # noqa: TC001
from roots_of_rhythm.discovery.application.queries.song_overview import SongOverviewReader  # noqa: TC001
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_songs_router() -> Router:
    @get()
    async def list_published_songs(
        song_list_reader: NamedDependency[SongListReader],
    ) -> SongListResponse | Response[ErrorResponse]:
        try:
            return await song_list_reader.list()
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to list published Songs", extra={"request_id": request_id})
            return _error_response(500, "INTERNAL_ERROR", _INTERNAL_ERROR_MESSAGE, request_id=request_id)

    @get("/{song_id:str}")
    async def get_published_song_overview(
        song_id: FromPath[str],
        song_overview_reader: NamedDependency[SongOverviewReader],
    ) -> SongOverviewResponse | Response[ErrorResponse]:
        try:
            parsed_id = UUID(song_id)
        except ValueError:
            return _error_response(404, "SONG_NOT_FOUND", _NOT_FOUND_MESSAGE)
        try:
            return await song_overview_reader.get(parsed_id)
        except SongOverviewNotFound:
            return _error_response(404, "SONG_NOT_FOUND", _NOT_FOUND_MESSAGE)
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Song overview", extra={"request_id": request_id})
            return _error_response(500, "INTERNAL_ERROR", _INTERNAL_ERROR_MESSAGE, request_id=request_id)

    return Router(
        path="/api/v1/songs",
        route_handlers=[list_published_songs, get_published_song_overview],
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
