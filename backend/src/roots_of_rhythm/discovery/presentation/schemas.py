import msgspec


class ErrorResponse(msgspec.Struct, frozen=True):
    code: str
    message: str
    details: dict[str, object] | None
    request_id: str | None
