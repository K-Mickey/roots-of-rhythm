from roots_of_rhythm.music_catalog.domain import (
    EditorialStatus,
    EvidenceStatus,
    ExternalIdentity,
    MusicalWork,
    WorkContent,
    WorkCredit,
    WorkCreditContent,
    WorkCreditRole,
    WorkRelation,
    WorkRelationContent,
    WorkRelationType,
)
from roots_of_rhythm.music_catalog.infrastructure.mapping._temporal import (
    apply_existence_period_columns,
    existence_period_from_columns,
)
from roots_of_rhythm.music_catalog.infrastructure.models import MusicalWorkRecord, WorkCreditRecord, WorkRelationRecord


def record_from_musical_work(work: MusicalWork) -> MusicalWorkRecord:
    record = MusicalWorkRecord(
        id=work.id,
        editorial_status=work.editorial_status.value,
        canonical_title=work.canonical_title,
        aliases=list(work.aliases),
        description=work.description,
        external_identities=[
            {"provider": identity.provider, "identifier": identity.identifier, "url": identity.url}
            for identity in work.external_identities
        ],
        provenance=work.provenance,
    )
    apply_existence_period_columns(record, work.period)
    return record


def musical_work_from_record(record: MusicalWorkRecord) -> MusicalWork:
    return MusicalWork.create(
        record.id,
        WorkContent.create(
            record.canonical_title,
            aliases=tuple(record.aliases),
            description=record.description,
            period=existence_period_from_columns(
                record.period_start_year,
                record.period_start_precision,
                record.period_end_year,
                record.period_end_precision,
            ),
            external_identities=tuple(
                ExternalIdentity.create(
                    identity["provider"],
                    identity["identifier"],
                    url=identity["url"],
                )
                for identity in record.external_identities
            ),
            provenance=record.provenance,
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_musical_work_record(record: MusicalWorkRecord, work: MusicalWork) -> None:
    record.editorial_status = work.editorial_status.value
    record.canonical_title = work.canonical_title
    record.aliases = list(work.aliases)
    record.description = work.description
    record.external_identities = [
        {"provider": identity.provider, "identifier": identity.identifier, "url": identity.url}
        for identity in work.external_identities
    ]
    record.provenance = work.provenance
    apply_existence_period_columns(record, work.period)


def record_from_work_credit(credit: WorkCredit) -> WorkCreditRecord:
    return WorkCreditRecord(
        id=credit.id,
        work_id=credit.work_id,
        person_id=credit.person_id,
        role=credit.role.value,
        credited_as=credit.credited_as,
        provenance=credit.provenance,
        editorial_status=credit.editorial_status.value,
    )


def work_credit_from_record(record: WorkCreditRecord) -> WorkCredit:
    return WorkCredit.create(
        record.id,
        record.work_id,
        record.person_id,
        WorkCreditRole(record.role),
        WorkCreditContent.create(
            role=WorkCreditRole(record.role),
            credited_as=record.credited_as,
            provenance=record.provenance,
        ),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_work_credit_record(record: WorkCreditRecord, credit: WorkCredit) -> None:
    record.work_id = credit.work_id
    record.person_id = credit.person_id
    record.role = credit.role.value
    record.credited_as = credit.credited_as
    record.provenance = credit.provenance
    record.editorial_status = credit.editorial_status.value


def record_from_work_relation(relation: WorkRelation) -> WorkRelationRecord:
    return WorkRelationRecord(
        id=relation.id,
        source_work_id=relation.source_work_id,
        target_work_id=relation.target_work_id,
        relation_type=relation.relation_type.value,
        provenance=relation.provenance,
        evidence_status=relation.evidence_status.value,
        editorial_status=relation.editorial_status.value,
    )


def work_relation_from_record(record: WorkRelationRecord) -> WorkRelation:
    relation_type = WorkRelationType(record.relation_type)
    return WorkRelation.create(
        record.id,
        record.source_work_id,
        record.target_work_id,
        relation_type,
        WorkRelationContent.create(
            relation_type=relation_type,
            provenance=record.provenance,
        ),
        evidence_status=EvidenceStatus(record.evidence_status),
        editorial_status=EditorialStatus(record.editorial_status),
    )


def update_work_relation_record(record: WorkRelationRecord, relation: WorkRelation) -> None:
    record.source_work_id = relation.source_work_id
    record.target_work_id = relation.target_work_id
    record.relation_type = relation.relation_type.value
    record.provenance = relation.provenance
    record.evidence_status = relation.evidence_status.value
    record.editorial_status = relation.editorial_status.value
