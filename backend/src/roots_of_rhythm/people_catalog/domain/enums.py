from enum import StrEnum


class EditorialStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TemporalPrecision(StrEnum):
    EXACT_YEAR = "exact_year"
    CIRCA_YEAR = "circa_year"
    DECADE = "decade"
    EARLY_DECADE = "early_decade"
    MID_DECADE = "mid_decade"
    LATE_DECADE = "late_decade"
