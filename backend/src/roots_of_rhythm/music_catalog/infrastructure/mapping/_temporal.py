from typing import TYPE_CHECKING

from roots_of_rhythm.music_catalog.domain import ExistencePeriod, TemporalBound, TemporalPrecision

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.infrastructure.models import (
        GroupMembershipRecord,
        GroupRecord,
        MusicalWorkRecord,
    )


def temporal_bound(year: int | None, precision: str | None) -> TemporalBound | None:
    if year is None or precision is None:
        return None
    return TemporalBound(year=year, precision=TemporalPrecision(precision))


def existence_period_from_columns(
    start_year: int | None,
    start_precision: str | None,
    end_year: int | None,
    end_precision: str | None,
) -> ExistencePeriod | None:
    start = temporal_bound(start_year, start_precision)
    end = temporal_bound(end_year, end_precision)
    if start is None and end is None:
        return None
    return ExistencePeriod(start=start, end=end)


def apply_existence_period_columns(
    record: GroupRecord | GroupMembershipRecord | MusicalWorkRecord,
    period: ExistencePeriod | None,
) -> None:
    start = period.start if period is not None else None
    end = period.end if period is not None else None
    record.period_start_year = start.year if start is not None else None
    record.period_start_precision = start.precision.value if start is not None else None
    record.period_end_year = end.year if end is not None else None
    record.period_end_precision = end.precision.value if end is not None else None
