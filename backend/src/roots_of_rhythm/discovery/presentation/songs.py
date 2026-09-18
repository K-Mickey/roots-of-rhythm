import logging
from http import HTTPStatus
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency
from litestar.params import FromPath
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto.songs import SongListResponse, SongOverviewResponse
from roots_of_rhythm.discovery.application.errors.songs import SongOverviewNotFound
from roots_of_rhythm.discovery.application.queries.song_list import SongListReader
from roots_of_rhythm.discovery.application.queries.song_overview import SongOverviewReader
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)
_NOT_FOUND_MESSAGE = "Материал не найден."
_INTERNAL_ERROR_MESSAGE = "Не удалось загрузить материал."


def create_songs_router() -> Router:
    return Router(
        path="/songs",
        route_handlers=[
            list_published_songs,
            get_published_song_overview,
        ],
    )


@get()
async def list_published_songs(
    song_list_reader: NamedDependency[SongListReader],
) -> SongListResponse | Response[ErrorResponse]:
    try:
        return await song_list_reader.list()
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to list published Songs", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message=_INTERNAL_ERROR_MESSAGE,
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@get("/{song_id:str}")
async def get_published_song_overview(
    song_id: FromPath[str],
    song_overview_reader: NamedDependency[SongOverviewReader],
) -> SongOverviewResponse | Response[ErrorResponse]:
    try:
        parsed_id = UUID(song_id)
    except ValueError:
        return Response(
            ErrorResponse(
                code="SONG_NOT_FOUND",
                message=_NOT_FOUND_MESSAGE,
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    try:
        return await song_overview_reader.get(parsed_id)
    except SongOverviewNotFound:
        return Response(
            ErrorResponse(
                code="SONG_NOT_FOUND",
                message=_NOT_FOUND_MESSAGE,
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to assemble Song overview", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message=_INTERNAL_ERROR_MESSAGE,
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
