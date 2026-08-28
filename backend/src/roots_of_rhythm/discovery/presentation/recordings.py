import logging
from uuid import UUID, uuid7

from litestar import Router, get
from litestar.di import NamedDependency  # noqa: TC002 - Litestar inspects annotations
from litestar.params import FromPath  # noqa: TC002 - Litestar inspects annotations
from litestar.response import Response

from roots_of_rhythm.discovery.application.dto import RecordingOverviewResponse  # noqa: TC001
from roots_of_rhythm.discovery.application.errors import RecordingOverviewNotFound
from roots_of_rhythm.discovery.application.recording_overview import RecordingOverviewReader  # noqa: TC001
from roots_of_rhythm.discovery.presentation.schemas import ErrorResponse

logger = logging.getLogger(__name__)


def create_recordings_router() -> Router:
    @get("/{recording_id:str}")
    async def get_recording(
        recording_id: FromPath[str],
        recording_overview_reader: NamedDependency[RecordingOverviewReader],
    ) -> RecordingOverviewResponse | Response[ErrorResponse]:
        try:
            parsed = UUID(recording_id)
        except ValueError:
            return _error(404, "RECORDING_NOT_FOUND", "Запись не найдена.")
        try:
            return await recording_overview_reader.get(parsed)
        except RecordingOverviewNotFound:
            return _error(404, "RECORDING_NOT_FOUND", "Запись не найдена.")
        except Exception:
            request_id = str(uuid7())
            logger.exception("Failed to assemble Recording overview", extra={"request_id": request_id})
            return _error(500, "INTERNAL_ERROR", "Не удалось загрузить запись.", request_id)

    return Router(path="/api/v1/recordings", route_handlers=[get_recording])


def _error(status: int, code: str, message: str, request_id: str | None = None) -> Response[ErrorResponse]:
    return Response(ErrorResponse(code, message, None, request_id or str(uuid7())), status_code=status)
