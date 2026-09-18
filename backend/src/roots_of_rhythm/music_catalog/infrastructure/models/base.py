from roots_of_rhythm.infrastructure.models import BaseModel
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
from roots_of_rhythm.utils.sql import enum_in_check

CLASSIFICATION_CONCEPT_NAME_UNIQUE_CONSTRAINT = "uq_classification_concepts_kind_canonical_name_ci"

KIND_CHECK = enum_in_check("kind", ClassificationKind)
TARGET_KIND_CHECK = enum_in_check("target_kind", ClassificationTargetKind)
EDITORIAL_STATUS_CHECK = enum_in_check("editorial_status", EditorialStatus)
EVIDENCE_STATUS_CHECK = enum_in_check("evidence_status", EvidenceStatus)
WORK_CREDIT_ROLE_CHECK = enum_in_check("role", WorkCreditRole)
WORK_RELATION_TYPE_CHECK = enum_in_check("relation_type", WorkRelationType)
LYRICS_USAGE_KIND_CHECK = enum_in_check("usage_kind", LyricsUsageKind)
LYRICS_CREATION_METHOD_CHECK = enum_in_check("creation_method", LyricsCreationMethod)
LYRICS_VERSION_RELATION_TYPE_CHECK = enum_in_check("relation_type", LyricsVersionRelationType)
RECORDING_CREDIT_TARGET_KIND_CHECK = enum_in_check("target_kind", RecordingCreditTargetKind)
BILLING_ROLE_CHECK = enum_in_check("billing_role", BillingRole)
RECORDING_CONTRIBUTION_KIND_CHECK = (
    f"contribution_kind IS NULL OR {enum_in_check('contribution_kind', RecordingContributionKind)}"
)
RECORDING_WORK_USAGE_KIND_CHECK = enum_in_check("usage_kind", RecordingWorkUsageKind)
CLASSIFICATION_ASSIGNMENT_UNIQUE_CONSTRAINT = "uq_classification_assignments_target_concept"

WORK_CREDIT_UNIQUE_CONSTRAINT = "uq_work_credits_work_person_role"
WORK_RELATION_UNIQUE_CONSTRAINT = "uq_work_relations_source_target_type"
LYRICS_VERSION_UNIQUE_CONSTRAINT = "uq_lyrics_versions_work_language_usage_label"
LYRICS_VERSION_CREDIT_UNIQUE_CONSTRAINT = "uq_lyrics_version_credits_version_person_role"
LYRICS_VERSION_RELATION_UNIQUE_CONSTRAINT = "uq_lyrics_version_relations_source_target_type"
RECORDING_WORK_USAGE_UNIQUE_CONSTRAINT = "uq_recording_work_usages_recording_work_kind"
RECORDING_LYRICS_VERSION_UNIQUE_CONSTRAINT = "uq_recording_lyrics_usages_recording_version"
RECORDING_LYRICS_POSITION_UNIQUE_CONSTRAINT = "uq_recording_lyrics_usages_recording_position"
TEMPORAL_PRECISION_CHECK = (
    "({year_column} IS NULL AND {precision_column} IS NULL) OR "
    "({year_column} IS NOT NULL AND {precision_column} IN "
    f"({', '.join(repr(precision.value) for precision in TemporalPrecision)}))"
)
PERIOD_START_YEAR_COLUMN = "period_start_year"
PERIOD_START_PRECISION_COLUMN = "period_start_precision"
PERIOD_END_YEAR_COLUMN = "period_end_year"
PERIOD_END_PRECISION_COLUMN = "period_end_precision"


class MusicCatalogBase(BaseModel):
    __abstract__ = True
