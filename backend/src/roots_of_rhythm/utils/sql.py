from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enum import Enum


def enum_in_check(column: str, enum_type: type[Enum]) -> str:
    return f"{column} IN ({', '.join(repr(item.value) for item in enum_type)})"
