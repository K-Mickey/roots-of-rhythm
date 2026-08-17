from collections.abc import Awaitable, Callable
from typing import Literal

import msgspec
from litestar import Router, get
from litestar.response import Response

type ReadinessProbe = Callable[[], Awaitable[bool]]
type HealthStatus = Literal["ok", "unavailable"]


class HealthResponse(msgspec.Struct, frozen=True):
    status: HealthStatus


def create_health_router(readiness_probe: ReadinessProbe) -> Router:
    @get("/live")
    async def liveness() -> HealthResponse:
        return HealthResponse(status="ok")

    @get("/ready")
    async def readiness() -> HealthResponse | Response[HealthResponse]:
        if not await readiness_probe():
            return Response(HealthResponse(status="unavailable"), status_code=503)
        return HealthResponse(status="ok")

    return Router(path="/health", route_handlers=[liveness, readiness])
