from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enum import Enum

    from sqlalchemy.exc import IntegrityError


def enum_in_check(column: str, enum_type: type[Enum]) -> str:
    return f"{column} IN ({', '.join(repr(item.value) for item in enum_type)})"


def is_unique_violation(exc: IntegrityError, unique_index: str) -> bool:
    orig = getattr(exc, "orig", None)
    diag = getattr(orig, "diag", None)
    constraint_name = getattr(diag, "constraint_name", None) or getattr(orig, "constraint_name", None)
    if constraint_name == unique_index:
        return True
    return unique_index in str(exc)
