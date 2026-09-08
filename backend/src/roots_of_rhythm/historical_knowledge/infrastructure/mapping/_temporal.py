from roots_of_rhythm.historical_knowledge.domain import TemporalBound, TemporalPrecision


def _bound(year: int | None, precision: str | None) -> TemporalBound | None:
    if year is None or precision is None:
        return None
    return TemporalBound(year=year, precision=TemporalPrecision(precision))
