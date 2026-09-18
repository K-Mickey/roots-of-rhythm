from roots_of_rhythm.historical_knowledge.domain.enums import (
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RecordingOriginPredicate,
    RelationType,
    SourceAccessPolicy,
)
from roots_of_rhythm.infrastructure.models import BaseModel
from roots_of_rhythm.utils.sql import enum_in_check

RECORDING_ORIGIN_PREDICATE_CHECK = enum_in_check("predicate", RecordingOriginPredicate)
RELATION_TYPE_CHECK = enum_in_check("relation_type", RelationType)
EDITORIAL_STATUS_CHECK = enum_in_check("editorial_status", EditorialStatus)
EVIDENCE_STATUS_CHECK = enum_in_check("evidence_status", EvidenceStatus)
EVIDENCE_ROLE_CHECK = enum_in_check("role", EvidenceRole)
FRAGMENT_REVIEW_CHECK = enum_in_check("review_status", FragmentReviewStatus)
SOURCE_ACCESS_POLICY_CHECK = enum_in_check("access_policy", SourceAccessPolicy)
CLAIM_ENDPOINTS_UNIQUE_INDEX = "uq_genre_relation_claims_endpoints_type"
RECORDING_ORIGIN_ENDPOINTS_UNIQUE_INDEX = "uq_recording_origin_claims_endpoints_predicate"


class HistoricalKnowledgeBase(BaseModel):
    __abstract__ = True
