from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersion,
    LyricsVersionContent,
    LyricsVersionCredit,
    LyricsVersionCreditContent,
    LyricsVersionRelation,
    LyricsVersionRelationContent,
    LyricsVersionRelationType,
    WorkCreditRole,
)
from roots_of_rhythm.music_catalog.infrastructure.models import (
    LyricsVersionCreditRecord,
    LyricsVersionRecord,
    LyricsVersionRelationRecord,
)


def record_from_lyrics_version(version: LyricsVersion) -> LyricsVersionRecord:
    return LyricsVersionRecord(
        id=version.id,
        work_id=version.work_id,
        source_version_id=version.source_version_id,
        language_tag=version.language_tag,
        usage_kind=version.usage_kind.value,
        creation_method=version.creation_method.value,
        label=version.label,
        body=version.body,
        provenance=version.provenance,
        editorial_status=version.editorial_status.value,
    )


def lyrics_version_from_record(record: LyricsVersionRecord) -> LyricsVersion:
    return LyricsVersion.create(
        record.id,
        record.work_id,
        record.source_version_id,
        LyricsVersionContent.create(
            language_tag=record.language_tag,
            usage_kind=LyricsUsageKind(record.usage_kind),
            creation_method=LyricsCreationMethod(record.creation_method),
            label=record.label,
            body=record.body,
            provenance=record.provenance,
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_lyrics_version_record(record: LyricsVersionRecord, version: LyricsVersion) -> None:
    record.work_id = version.work_id
    record.source_version_id = version.source_version_id
    record.language_tag = version.language_tag
    record.usage_kind = version.usage_kind.value
    record.creation_method = version.creation_method.value
    record.label = version.label
    record.body = version.body
    record.provenance = version.provenance
    record.editorial_status = version.editorial_status.value


def record_from_lyrics_version_credit(credit: LyricsVersionCredit) -> LyricsVersionCreditRecord:
    return LyricsVersionCreditRecord(
        id=credit.id,
        lyrics_version_id=credit.lyrics_version_id,
        person_id=credit.person_id,
        role=credit.role.value,
        credited_as=credit.credited_as,
        provenance=credit.provenance,
        editorial_status=credit.editorial_status.value,
    )


def lyrics_version_credit_from_record(record: LyricsVersionCreditRecord) -> LyricsVersionCredit:
    role = WorkCreditRole(record.role)
    return LyricsVersionCredit.create(
        record.id,
        record.lyrics_version_id,
        record.person_id,
        role,
        LyricsVersionCreditContent.create(
            role=role,
            credited_as=record.credited_as,
            provenance=record.provenance,
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_lyrics_version_credit_record(record: LyricsVersionCreditRecord, credit: LyricsVersionCredit) -> None:
    record.lyrics_version_id = credit.lyrics_version_id
    record.person_id = credit.person_id
    record.role = credit.role.value
    record.credited_as = credit.credited_as
    record.provenance = credit.provenance
    record.editorial_status = credit.editorial_status.value


def record_from_lyrics_version_relation(relation: LyricsVersionRelation) -> LyricsVersionRelationRecord:
    return LyricsVersionRelationRecord(
        id=relation.id,
        source_lyrics_version_id=relation.source_lyrics_version_id,
        target_lyrics_version_id=relation.target_lyrics_version_id,
        relation_type=relation.relation_type.value,
        provenance=relation.provenance,
        editorial_status=relation.editorial_status.value,
    )


def lyrics_version_relation_from_record(record: LyricsVersionRelationRecord) -> LyricsVersionRelation:
    relation_type = LyricsVersionRelationType(record.relation_type)
    return LyricsVersionRelation.create(
        record.id,
        record.source_lyrics_version_id,
        record.target_lyrics_version_id,
        relation_type,
        LyricsVersionRelationContent.create(
            relation_type=relation_type,
            provenance=record.provenance,
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_lyrics_version_relation_record(
    record: LyricsVersionRelationRecord,
    relation: LyricsVersionRelation,
) -> None:
    record.source_lyrics_version_id = relation.source_lyrics_version_id
    record.target_lyrics_version_id = relation.target_lyrics_version_id
    record.relation_type = relation.relation_type.value
    record.provenance = relation.provenance
    record.editorial_status = relation.editorial_status.value
