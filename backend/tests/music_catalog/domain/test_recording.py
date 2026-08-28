from uuid import uuid7

import pytest

from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    MusicCatalogDomainError,
    Recording,
    RecordingContent,
    RecordingContributionKind,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingPublicationError,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
)


def _credit(billing_role: BillingRole = BillingRole.PRIMARY) -> RecordingCredit:
    return RecordingCredit.create(
        uuid7(),
        RecordingCreditTargetKind.PERSON,
        uuid7(),
        billing_role,
        contribution_kind=RecordingContributionKind.INSTRUMENTAL,
        instrument=" guitar ",
        credited_as=" Artist ",
    )


def _usage(
    kind: RecordingWorkUsageKind = RecordingWorkUsageKind.COMPLETE,
    position: int | None = None,
) -> RecordingWorkUsage:
    return RecordingWorkUsage.create(uuid7(), uuid7(), kind, position=position)


def test_recording_normalizes_isrc_and_requires_primary_credit_to_publish() -> None:
    credit = _credit()
    recording = Recording.create(
        uuid7(),
        RecordingContent.create(
            " Take One ",
            isrc="US-AAA-26-00001",
            recording_credits=(credit,),
            work_usages=(_usage(),),
        ),
    ).publish()

    assert recording.title == "Take One"
    assert recording.isrc == "USAAA2600001"
    assert recording.credits[0].instrument == "guitar"
    assert recording.credits[0].credited_as == "Artist"

    without_primary = Recording.create(
        uuid7(),
        RecordingContent.create("Take Two", recording_credits=(_credit(BillingRole.ADDITIONAL),)),
    )
    with pytest.raises(RecordingPublicationError, match="primary_credit"):
        without_primary.publish()
    with pytest.raises(RecordingPublicationError, match="primary_credit"):
        recording.replace_content(RecordingContent.create("Invalid published replacement"))

    primary_only = Recording.create(
        uuid7(),
        RecordingContent.create("No work", recording_credits=(_credit(),)),
    )
    with pytest.raises(RecordingPublicationError) as error:
        primary_only.publish()
    assert error.value.missing_fields == ("work_usage",)

    empty = Recording.create(uuid7(), RecordingContent.create("Empty"))
    with pytest.raises(RecordingPublicationError) as error:
        empty.publish()
    assert error.value.missing_fields == ("primary_credit", "work_usage")


def test_recording_accepts_partial_usage_and_rejects_duplicate_usage() -> None:
    work_id = uuid7()
    partial = RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.PARTIAL)

    content = RecordingContent.create("Excerpt", work_usages=(partial,))
    assert content.work_usages == (partial,)

    duplicate = RecordingWorkUsage.create(uuid7(), work_id, RecordingWorkUsageKind.PARTIAL)
    with pytest.raises(MusicCatalogDomainError, match="duplicate work"):
        RecordingContent.create("Duplicate", work_usages=(partial, duplicate))


def test_multiple_medley_components_require_unique_positive_positions() -> None:
    first = _usage(RecordingWorkUsageKind.MEDLEY_COMPONENT, 1)
    second = _usage(RecordingWorkUsageKind.MEDLEY_COMPONENT, 2)
    assert RecordingContent.create("Medley", work_usages=(first, second)).work_usages == (first, second)

    with pytest.raises(MusicCatalogDomainError, match="require positions"):
        RecordingContent.create(
            "Missing position",
            work_usages=(first, _usage(RecordingWorkUsageKind.MEDLEY_COMPONENT)),
        )
    with pytest.raises(MusicCatalogDomainError, match="positions must be unique"):
        RecordingContent.create(
            "Duplicate position",
            work_usages=(first, _usage(RecordingWorkUsageKind.MEDLEY_COMPONENT, 1)),
        )
    with pytest.raises(MusicCatalogDomainError, match="position must be positive"):
        _usage(RecordingWorkUsageKind.MEDLEY_COMPONENT, 0)


def test_recording_rejects_mixed_or_multiple_non_medley_usages() -> None:
    with pytest.raises(MusicCatalogDomainError, match="one usage kind"):
        RecordingContent.create(
            "Mixed",
            work_usages=(_usage(), _usage(RecordingWorkUsageKind.MEDLEY_COMPONENT)),
        )
    with pytest.raises(MusicCatalogDomainError, match="exactly one"):
        RecordingContent.create("Two complete", work_usages=(_usage(), _usage()))
    with pytest.raises(MusicCatalogDomainError, match="exactly one"):
        RecordingContent.create(
            "Two partial",
            work_usages=(_usage(RecordingWorkUsageKind.PARTIAL), _usage(RecordingWorkUsageKind.PARTIAL)),
        )


def test_recording_rejects_invalid_isrc() -> None:
    with pytest.raises(MusicCatalogDomainError, match="ISRC"):
        RecordingContent.create("Bad code", isrc="invalid")
