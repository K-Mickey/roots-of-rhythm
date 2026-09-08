from roots_of_rhythm.historical_knowledge.domain import (
    FragmentReviewStatus,
    Source,
    SourceAccessPolicy,
    SourceFragment,
    SourceVersion,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)


def source_from_record(record: SourceRecord) -> Source:
    return Source(
        id=record.id,
        title=record.title,
        author=record.author,
        responsible_organization=record.responsible_organization,
        publication=record.publication,
        publication_date=record.publication_date,
        external_url=record.external_url,
        access_policy=SourceAccessPolicy(record.access_policy),
    )


def record_from_source(source: Source) -> SourceRecord:
    return SourceRecord(
        id=source.id,
        title=source.title,
        author=source.author,
        responsible_organization=source.responsible_organization,
        publication=source.publication,
        publication_date=source.publication_date,
        external_url=source.external_url,
        access_policy=source.access_policy.value,
    )


def version_from_record(record: SourceVersionRecord) -> SourceVersion:
    return SourceVersion(id=record.id, source_id=record.source_id, label=record.label)


def record_from_version(version: SourceVersion) -> SourceVersionRecord:
    return SourceVersionRecord(id=version.id, source_id=version.source_id, label=version.label)


def fragment_from_record(record: SourceFragmentRecord) -> SourceFragment:
    return SourceFragment(
        id=record.id,
        source_version_id=record.source_version_id,
        review_status=FragmentReviewStatus(record.review_status),
        locator_text=record.locator_text,
        external_url=record.external_url,
    )


def record_from_fragment(fragment: SourceFragment) -> SourceFragmentRecord:
    return SourceFragmentRecord(
        id=fragment.id,
        source_version_id=fragment.source_version_id,
        review_status=fragment.review_status.value,
        locator_text=fragment.locator_text,
        external_url=fragment.external_url,
    )


def update_fragment_record(record: SourceFragmentRecord, fragment: SourceFragment) -> None:
    # Leave created_at / updated_at / deleted alone (DB trigger + soft-delete path).
    record.review_status = fragment.review_status.value
    record.locator_text = fragment.locator_text
    record.external_url = fragment.external_url
