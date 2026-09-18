class _FakeSession:
    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def execute(self, *args: object, **kwargs: object) -> object:  # noqa: ARG002
        return object()
