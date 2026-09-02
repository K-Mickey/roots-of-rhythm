from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    ClassificationAssignment,
    ClassificationAssignmentPublicationError,
    EvidenceStatus,
)


def test_assignment_publication_rejects_missing_explanation_or_claim() -> None:
    assignment = ClassificationAssignment.create_for_person(
        uuid7(),
        uuid7(),
        uuid7(),
        provenance="Editorial review.",
    )

    with pytest.raises(ClassificationAssignmentPublicationError) as error:
        assignment.publish()

    assert error.value.invalid_fields == ("explanation_or_claim_id",)


def test_assignment_publication_rejects_missing_provenance() -> None:
    assignment = ClassificationAssignment.create_for_person(
        uuid7(),
        uuid7(),
        uuid7(),
        explanation="A Jazz performer.",
    )

    with pytest.raises(ClassificationAssignmentPublicationError) as error:
        assignment.publish()

    assert error.value.invalid_fields == ("provenance",)


def test_assignment_publication_rejects_supported_without_evidence_refs() -> None:
    assignment = ClassificationAssignment.create_for_person(
        uuid7(),
        uuid7(),
        uuid7(),
        explanation="A Jazz performer.",
        provenance="Editorial review.",
        evidence_status=EvidenceStatus.SUPPORTED,
    )

    with pytest.raises(ClassificationAssignmentPublicationError) as error:
        assignment.publish()

    assert error.value.invalid_fields == ("evidence_status",)


def test_assignment_publication_accepts_explanation() -> None:
    assignment = ClassificationAssignment.create_for_person(
        uuid7(),
        uuid7(),
        uuid7(),
        explanation="Editorial explanation",
        provenance="Editorial review.",
    )

    published = assignment.publish()

    assert published.is_published
    assert published.id == assignment.id


def test_assignment_publication_accepts_claim_id() -> None:
    claim_id = uuid7()
    assignment = ClassificationAssignment.create_for_person(
        uuid7(),
        uuid7(),
        uuid7(),
        claim_id=claim_id,
        provenance="Editorial review.",
    )

    published = assignment.publish()

    assert published.is_published
    assert published.claim_id == claim_id


def test_group_assignment_publication_does_not_require_membership() -> None:
    assignment = ClassificationAssignment.create_for_group(
        uuid7(),
        uuid7(),
        uuid7(),
        explanation="A Jazz group.",
        provenance="Editorial review.",
    )

    published = assignment.publish()

    assert published.is_published


def test_assignment_replace_content_preserves_identity_and_status() -> None:
    assignment_id = uuid7()
    person_id = uuid7()
    concept_id = uuid7()
    published = ClassificationAssignment.create_for_person(
        assignment_id,
        person_id,
        concept_id,
        explanation="Draft explanation.",
        provenance="Draft provenance.",
    ).publish()

    updated = published.replace_content(
        explanation="Seed explanation.",
        claim_id=None,
        provenance="Seed provenance.",
        evidence_status=EvidenceStatus.UNVERIFIED,
    )

    assert updated.id == assignment_id
    assert updated.target_id == person_id
    assert updated.concept_id == concept_id
    assert updated.is_published
    assert updated.explanation == "Seed explanation."
    assert updated.provenance == "Seed provenance."
