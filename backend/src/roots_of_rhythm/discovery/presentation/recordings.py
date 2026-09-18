import logging
from http import HTTPStatus
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency
from litestar.params import FromPath
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto.recordings import RecordingListResponse, RecordingOverviewResponse
from roots_of_rhythm.discovery.application.errors.recordings import RecordingOverviewNotFound
from roots_of_rhythm.discovery.application.queries.recording_list import RecordingListReader
from roots_of_rhythm.discovery.application.queries.recording_overview import RecordingOverviewReader
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)


def create_recordings_router() -> Router:
    return Router(
        path="/recordings",
        route_handlers=[
            list_recordings,
            get_recording,
        ],
    )


@get()
async def list_recordings(
    recording_list_reader: NamedDependency[RecordingListReader],
) -> RecordingListResponse | Response[ErrorResponse]:
    try:
        return await recording_list_reader.list()
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to list published Recordings", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message="Не удалось загрузить записи.",
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@get("/{recording_id:str}")
async def get_recording(
    recording_id: FromPath[str],
    recording_overview_reader: NamedDependency[RecordingOverviewReader],
) -> RecordingOverviewResponse | Response[ErrorResponse]:
    try:
        parsed = UUID(recording_id)
    except ValueError:
        return Response(
            ErrorResponse(
                code="RECORDING_NOT_FOUND",
                message="Запись не найдена.",
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    try:
        return await recording_overview_reader.get(parsed)
    except RecordingOverviewNotFound:
        return Response(
            ErrorResponse(
                code="RECORDING_NOT_FOUND",
                message="Запись не найдена.",
                details=None,
                request_id=str(uuid7()),
            ),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except Exception:
        request_id = str(uuid7())
        logger.exception("Failed to assemble Recording overview", extra={"request_id": request_id})
        return Response(
            ErrorResponse(
                code="INTERNAL_ERROR",
                message="Не удалось загрузить запись.",
                details=None,
                request_id=request_id,
            ),
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
