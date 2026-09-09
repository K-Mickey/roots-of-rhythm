from typing import Self
from uuid import UUID, uuid7

import msgspec

from roots_of_rhythm.historical_knowledge.domain import HistoricalKnowledgeDomainError
from roots_of_rhythm.historical_knowledge.domain.enums import FragmentReviewStatus, SourceAccessPolicy
from roots_of_rhythm.utils.text import optional_text, required_text
from roots_of_rhythm.utils.text_lengths import TEXT_64, TEXT_1024, TEXT_2048


class Source(msgspec.Struct, frozen=True):
    id: UUID
    title: str
    author: str | None = None
    responsible_organization: str | None = None
    publication: str | None = None
    publication_date: str | None = None
    external_url: str | None = None
    access_policy: SourceAccessPolicy = SourceAccessPolicy.WITHHOLD_PUBLIC_BODY

    @classmethod
    def create(
        cls,
        title: str,
        *,
        author: str | None = None,
        responsible_organization: str | None = None,
        publication: str | None = None,
        publication_date: str | None = None,
        external_url: str | None = None,
        access_policy: SourceAccessPolicy = SourceAccessPolicy.WITHHOLD_PUBLIC_BODY,
        source_id: UUID | None = None,
    ) -> Self:
        return cls(
            id=source_id or uuid7(),
            title=required_text(title, "source title", max_length=TEXT_64, error=HistoricalKnowledgeDomainError),
            author=optional_text(author, "author", max_length=TEXT_64, error=HistoricalKnowledgeDomainError),
            responsible_organization=optional_text(
                responsible_organization,
                "responsible organization",
                max_length=TEXT_64,
                error=HistoricalKnowledgeDomainError,
            ),
            publication=optional_text(
                publication, "publication", max_length=TEXT_64, error=HistoricalKnowledgeDomainError
            ),
            publication_date=optional_text(
                publication_date,
                "publication date",
                max_length=TEXT_64,
                error=HistoricalKnowledgeDomainError,
            ),
            external_url=optional_text(
                external_url, "external url", max_length=TEXT_2048, error=HistoricalKnowledgeDomainError
            ),
            access_policy=access_policy,
        )

    @property
    def is_allow_public_body(self) -> bool:
        return self.access_policy is SourceAccessPolicy.ALLOW_PUBLIC_BODY

    def with_access_policy(self, access_policy: SourceAccessPolicy) -> Self:
        return msgspec.structs.replace(self, access_policy=access_policy)


class SourceVersion(msgspec.Struct, frozen=True):
    id: UUID
    source_id: UUID
    label: str

    @classmethod
    def create(cls, source_id: UUID, label: str, *, version_id: UUID | None = None) -> Self:
        return cls(
            id=version_id or uuid7(),
            source_id=source_id,
            label=required_text(label, "version label", max_length=TEXT_64, error=HistoricalKnowledgeDomainError),
        )


class SourceFragment(msgspec.Struct, frozen=True):
    id: UUID
    source_version_id: UUID
    review_status: FragmentReviewStatus = FragmentReviewStatus.PENDING
    locator_text: str | None = None
    external_url: str | None = None

    @classmethod
    def create(
        cls,
        source_version_id: UUID,
        *,
        locator_text: str | None = None,
        external_url: str | None = None,
        fragment_id: UUID | None = None,
    ) -> Self:
        return cls(
            id=fragment_id or uuid7(),
            source_version_id=source_version_id,
            locator_text=optional_text(
                locator_text, "locator text", max_length=TEXT_1024, error=HistoricalKnowledgeDomainError
            ),
            external_url=optional_text(
                external_url, "external url", max_length=TEXT_2048, error=HistoricalKnowledgeDomainError
            ),
        )

    @property
    def is_reviewed(self) -> bool:
        return self.review_status is FragmentReviewStatus.REVIEWED

    def mark_reviewed(self) -> "SourceFragment":
        return SourceFragment(
            id=self.id,
            source_version_id=self.source_version_id,
            review_status=FragmentReviewStatus.REVIEWED,
            locator_text=self.locator_text,
            external_url=self.external_url,
        )
