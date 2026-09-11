import asyncio
import inspect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


async def wait_until_async(
    predicate: "Callable[[], Awaitable[bool] | bool]",
    *,
    timeout_seconds: float = 10.0,
    interval_seconds: float = 0.1,
    message: str = "Timed out waiting for condition",
) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds
    while True:
        result = predicate()
        if inspect.isawaitable(result):
            result = await result
        if result:
            return
        if loop.time() >= deadline:
            raise AssertionError(message)
        await asyncio.sleep(interval_seconds)
