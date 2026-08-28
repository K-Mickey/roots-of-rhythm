from roots_of_rhythm.music_catalog.domain import (
    BillingRole,
    EditorialStatus,
    Recording,
    RecordingContent,
    RecordingContributionKind,
    RecordingCredit,
    RecordingCreditTargetKind,
    RecordingLyricsUsage,
    RecordingWorkUsage,
    RecordingWorkUsageKind,
)
from roots_of_rhythm.music_catalog.infrastructure.mapping._temporal import (
    apply_existence_period_columns,
    existence_period_from_columns,
)
from roots_of_rhythm.music_catalog.infrastructure.models import (
    RecordingCreditRecord,
    RecordingLyricsUsageRecord,
    RecordingRecord,
    RecordingWorkUsageRecord,
)


def record_from_recording(recording: Recording) -> RecordingRecord:
    record = RecordingRecord(
        id=recording.id,
        title=recording.title,
        description=recording.description,
        isrc=recording.isrc,
        editorial_status=recording.editorial_status.value,
    )
    apply_existence_period_columns(record, recording.recorded_period)
    return record


def recording_from_records(
    record: RecordingRecord,
    credit_records: list[RecordingCreditRecord],
    usages: list[RecordingWorkUsageRecord],
    lyrics_usages: list[RecordingLyricsUsageRecord],
) -> Recording:
    return Recording.create(
        record.id,
        RecordingContent.create(
            record.title,
            recorded_period=existence_period_from_columns(
                record.period_start_year,
                record.period_start_precision,
                record.period_end_year,
                record.period_end_precision,
            ),
            description=record.description,
            isrc=record.isrc,
            recording_credits=tuple(
                RecordingCredit.create(
                    credit.id,
                    RecordingCreditTargetKind(credit.target_kind),
                    credit.target_id,
                    BillingRole(credit.billing_role),
                    contribution_kind=(
                        RecordingContributionKind(credit.contribution_kind)
                        if credit.contribution_kind is not None
                        else None
                    ),
                    instrument=credit.instrument,
                    credited_as=credit.credited_as,
                )
                for credit in credit_records
            ),
            work_usages=tuple(
                RecordingWorkUsage.create(
                    usage.id,
                    usage.work_id,
                    RecordingWorkUsageKind(usage.usage_kind),
                    position=usage.position,
                )
                for usage in usages
            ),
            lyrics_usages=tuple(
                RecordingLyricsUsage.create(usage.id, usage.lyrics_version_id) for usage in lyrics_usages
            ),
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_recording_record(record: RecordingRecord, recording: Recording) -> None:
    record.title = recording.title
    record.description = recording.description
    record.isrc = recording.isrc
    record.editorial_status = recording.editorial_status.value
    apply_existence_period_columns(record, recording.recorded_period)


def records_from_recording_children(
    recording: Recording,
) -> tuple[list[RecordingCreditRecord], list[RecordingWorkUsageRecord], list[RecordingLyricsUsageRecord]]:
    credit_records = [
        RecordingCreditRecord(
            id=credit.id,
            recording_id=recording.id,
            target_kind=credit.target_kind.value,
            target_id=credit.target_id,
            billing_role=credit.billing_role.value,
            contribution_kind=credit.contribution_kind.value if credit.contribution_kind is not None else None,
            instrument=credit.instrument,
            credited_as=credit.credited_as,
        )
        for credit in recording.credits
    ]
    usages = [
        RecordingWorkUsageRecord(
            id=usage.id,
            recording_id=recording.id,
            work_id=usage.work_id,
            usage_kind=usage.usage_kind.value,
            position=usage.position,
        )
        for usage in recording.work_usages
    ]
    lyrics_usages = [
        RecordingLyricsUsageRecord(
            id=usage.id,
            recording_id=recording.id,
            lyrics_version_id=usage.lyrics_version_id,
            position=usage.position,
        )
        for usage in recording.lyrics_usages
    ]
    return credit_records, usages, lyrics_usages
