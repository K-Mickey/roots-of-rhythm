from __future__ import annotations

from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

_LeftT = TypeVar("_LeftT")
_RightT = TypeVar("_RightT")


def pair_scope(
    left_factory: Callable[[], _LeftT],
    right_factory: Callable[[], _RightT],
) -> Callable[[], AbstractAsyncContextManager[tuple[_LeftT, _RightT]]]:
    @asynccontextmanager
    async def scope() -> AsyncIterator[tuple[_LeftT, _RightT]]:
        yield left_factory(), right_factory()

    return scope
