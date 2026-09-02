from __future__ import annotations

from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    WorkCredit,
    WorkCreditContent,
    WorkCreditRole,
    WorkRelation,
    WorkRelationContent,
    WorkRelationPublicationError,
    WorkRelationSelfReferenceError,
    WorkRelationType,
)


def test_work_credit_allows_multiple_roles_for_same_person() -> None:
    work_id = uuid7()
    person_id = uuid7()
    composer = WorkCredit.create(
        uuid7(),
        work_id,
        person_id,
        WorkCreditRole.COMPOSER,
        WorkCreditContent.create(role=WorkCreditRole.COMPOSER),
    )
    lyricist = WorkCredit.create(
        uuid7(),
        work_id,
        person_id,
        WorkCreditRole.LYRICIST,
        WorkCreditContent.create(role=WorkCreditRole.LYRICIST, credited_as="Lyric pen name"),
    )

    assert composer.is_composer
    assert lyricist.is_lyricist
    assert lyricist.credited_as == "Lyric pen name"


def test_work_credit_publish_without_required_person_fields() -> None:
    credit = WorkCredit.create(
        uuid7(),
        uuid7(),
        uuid7(),
        WorkCreditRole.COMPOSER,
    )
    published = credit.publish()

    assert published.is_published


def test_work_relation_rejects_self_reference() -> None:
    work_id = uuid7()
    with pytest.raises(WorkRelationSelfReferenceError):
        WorkRelation.create(
            uuid7(),
            work_id,
            work_id,
            WorkRelationType.ADAPTATION_OF,
        )


def test_work_relation_publish_requires_provenance() -> None:
    relation = WorkRelation.create(
        uuid7(),
        uuid7(),
        uuid7(),
        WorkRelationType.TRANSLATION_OF,
    )
    with pytest.raises(WorkRelationPublicationError, match="provenance"):
        relation.publish()


def test_work_relation_publish_with_provenance() -> None:
    relation = WorkRelation.create(
        uuid7(),
        uuid7(),
        uuid7(),
        WorkRelationType.ARRANGEMENT_OF,
        WorkRelationContent.create(
            relation_type=WorkRelationType.ARRANGEMENT_OF,
            provenance="Editorial note.",
        ),
    )
    published = relation.publish()

    assert published.is_published
    assert published.provenance == "Editorial note."
