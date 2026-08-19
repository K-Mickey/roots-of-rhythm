from enum import StrEnum


class ClassificationKind(StrEnum):
    GENRE = "genre"
    STYLE = "style"
    SCENE = "scene"
    TRADITION = "tradition"


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


class ClassificationTargetKind(StrEnum):
    PERSON = "person"
    GROUP = "group"
    MUSICAL_WORK = "musical_work"
    RECORDING = "recording"
    RELEASE = "release"


class EvidenceStatus(StrEnum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    DISPUTED = "disputed"
