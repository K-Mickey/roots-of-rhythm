from enum import StrEnum


class RelationType(StrEnum):
    INFLUENCED = "influenced"
    CONTRIBUTED_TO_EMERGENCE_OF = "contributed_to_emergence_of"
    DEVELOPED_FROM = "developed_from"
    OVERLAPS_WITH = "overlaps_with"
    REVIVAL_OF = "revival_of"


class EditorialStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EvidenceStatus(StrEnum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    DISPUTED = "disputed"


class EvidenceRole(StrEnum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    CONTEXT = "context"


class FragmentReviewStatus(StrEnum):
    PENDING = "pending"
    REVIEWED = "reviewed"


class SourceAccessPolicy(StrEnum):
    ALLOW_PUBLIC_BODY = "allow_public_body"
    WITHHOLD_PUBLIC_BODY = "withhold_public_body"


class TemporalPrecision(StrEnum):
    EXACT_YEAR = "exact_year"
    CIRCA_YEAR = "circa_year"
    DECADE = "decade"
    EARLY_DECADE = "early_decade"
    MID_DECADE = "mid_decade"
    LATE_DECADE = "late_decade"
