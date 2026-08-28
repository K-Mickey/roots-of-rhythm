from sqlalchemy.orm import DeclarativeBase

from roots_of_rhythm.music_catalog.domain.enums import (
    BillingRole,
    ClassificationKind,
    ClassificationTargetKind,
    EditorialStatus,
    EvidenceStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionRelationType,
    RecordingContributionKind,
    RecordingCreditTargetKind,
    RecordingWorkUsageKind,
    TemporalPrecision,
    WorkCreditRole,
    WorkRelationType,
)

CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT = "uq_classification_concepts_kind_canonical_name_ci"

KIND_CHECK = f"kind IN ({', '.join(repr(kind.value) for kind in ClassificationKind)})"
TARGET_KIND_CHECK = f"target_kind IN ({', '.join(repr(kind.value) for kind in ClassificationTargetKind)})"
EDITORIAL_STATUS_CHECK = f"editorial_status IN ({', '.join(repr(status.value) for status in EditorialStatus)})"
EVIDENCE_STATUS_CHECK = f"evidence_status IN ({', '.join(repr(status.value) for status in EvidenceStatus)})"
WORK_CREDIT_ROLE_CHECK = f"role IN ({', '.join(repr(role.value) for role in WorkCreditRole)})"
WORK_RELATION_TYPE_CHECK = f"relation_type IN ({', '.join(repr(kind.value) for kind in WorkRelationType)})"
LYRICS_USAGE_KIND_CHECK = f"usage_kind IN ({', '.join(repr(kind.value) for kind in LyricsUsageKind)})"
LYRICS_CREATION_METHOD_CHECK = (
    f"creation_method IN ({', '.join(repr(method.value) for method in LyricsCreationMethod)})"
)
LYRICS_VERSION_RELATION_TYPE_CHECK = (
    f"relation_type IN ({', '.join(repr(kind.value) for kind in LyricsVersionRelationType)})"
)
RECORDING_CREDIT_TARGET_KIND_CHECK = (
    f"target_kind IN ({', '.join(repr(kind.value) for kind in RecordingCreditTargetKind)})"
)
BILLING_ROLE_CHECK = f"billing_role IN ({', '.join(repr(role.value) for role in BillingRole)})"
RECORDING_CONTRIBUTION_KIND_CHECK = (
    "contribution_kind IS NULL OR contribution_kind IN "
    f"({', '.join(repr(kind.value) for kind in RecordingContributionKind)})"
)
RECORDING_WORK_USAGE_KIND_CHECK = f"usage_kind IN ({', '.join(repr(kind.value) for kind in RecordingWorkUsageKind)})"
CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT = "uq_classification_assignments_target_concept"
WORK_CREDIT_UNIQUE_CONSTRAINT = "uq_work_credits_work_person_role"
WORK_RELATION_UNIQUE_CONSTRAINT = "uq_work_relations_source_target_type"
LYRICS_VERSION_UNIQUE_CONSTRAINT = "uq_lyrics_versions_work_language_usage_label"
LYRICS_VERSION_CREDIT_UNIQUE_CONSTRAINT = "uq_lyrics_version_credits_version_person_role"
LYRICS_VERSION_RELATION_UNIQUE_CONSTRAINT = "uq_lyrics_version_relations_source_target_type"
RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT = "uq_recording_work_usages_recording_work_kind"
TEMPORAL_PRECISION_CHECK = (
    "({year_column} IS NULL AND {precision_column} IS NULL) OR "
    "({year_column} IS NOT NULL AND {precision_column} IN "
    f"({', '.join(repr(precision.value) for precision in TemporalPrecision)}))"
)
PERIOD_START_YEAR_COLUMN = "period_start_year"
PERIOD_START_PRECISION_COLUMN = "period_start_precision"
PERIOD_END_YEAR_COLUMN = "period_end_year"
PERIOD_END_PRECISION_COLUMN = "period_end_precision"


class MusicCatalogBase(DeclarativeBase):
    pass
