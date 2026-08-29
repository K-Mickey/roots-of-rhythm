from sqlalchemy.orm import DeclarativeBase

from roots_of_rhythm.historical_knowledge.domain.enums import (
    EditorialStatus,
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RecordingOriginPredicate,
    RelationType,
    SourceAccessPolicy,
)

RECORDING_ORIGIN_PREDICATE_CHECK = (
    f"predicate IN ({', '.join(repr(item.value) for item in RecordingOriginPredicate)})"
)
RELATION_TYPE_CHECK = f"relation_type IN ({', '.join(repr(item.value) for item in RelationType)})"
EDITORIAL_STATUS_CHECK = f"editorial_status IN ({', '.join(repr(item.value) for item in EditorialStatus)})"
EVIDENCE_STATUS_CHECK = f"evidence_status IN ({', '.join(repr(item.value) for item in EvidenceStatus)})"
EVIDENCE_ROLE_CHECK = f"role IN ({', '.join(repr(item.value) for item in EvidenceRole)})"
FRAGMENT_REVIEW_CHECK = f"review_status IN ({', '.join(repr(item.value) for item in FragmentReviewStatus)})"
SOURCE_ACCESS_POLICY_CHECK = f"access_policy IN ({', '.join(repr(policy.value) for policy in SourceAccessPolicy)})"
CLAIM_ENDPOINTS_UNIQUE_INDEX = "uq_genre_relation_claims_endpoints_type"
RECORDING_ORIGIN_ENDPOINTS_UNIQUE_INDEX = "uq_recording_origin_claims_endpoints_predicate"


class HistoricalKnowledgeBase(DeclarativeBase):
    pass
