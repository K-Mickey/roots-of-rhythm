from typing import Self
from uuid import UUID, uuid7

import msgspec

from roots_of_rhythm.historical_knowledge.domain.enums import FragmentReviewStatus
from roots_of_rhythm.historical_knowledge.domain.value_objects import (
    LONG_TEXT_MAX_LENGTH,
    SHORT_TEXT_MAX_LENGTH,
    URL_MAX_LENGTH,
    _optional_text,
    _required_text,
)


class Source(msgspec.Struct, frozen=True):
    id: UUID
    title: str
    author: str | None = None
    responsible_organization: str | None = None
    publication: str | None = None
    publication_date: str | None = None
    external_url: str | None = None

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
        source_id: UUID | None = None,
    ) -> Self:
        return cls(
            id=source_id or uuid7(),
            title=_required_text(title, "source title", max_length=SHORT_TEXT_MAX_LENGTH),
            author=_optional_text(author, "author", max_length=SHORT_TEXT_MAX_LENGTH),
            responsible_organization=_optional_text(
                responsible_organization,
                "responsible organization",
                max_length=SHORT_TEXT_MAX_LENGTH,
            ),
            publication=_optional_text(publication, "publication", max_length=SHORT_TEXT_MAX_LENGTH),
            publication_date=_optional_text(
                publication_date,
                "publication date",
                max_length=SHORT_TEXT_MAX_LENGTH,
            ),
            external_url=_optional_text(external_url, "external url", max_length=URL_MAX_LENGTH),
        )


class SourceVersion(msgspec.Struct, frozen=True):
    id: UUID
    source_id: UUID
    label: str

    @classmethod
    def create(cls, source_id: UUID, label: str, *, version_id: UUID | None = None) -> Self:
        return cls(
            id=version_id or uuid7(),
            source_id=source_id,
            label=_required_text(label, "version label", max_length=SHORT_TEXT_MAX_LENGTH),
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
            locator_text=_optional_text(locator_text, "locator text", max_length=LONG_TEXT_MAX_LENGTH),
            external_url=_optional_text(external_url, "external url", max_length=URL_MAX_LENGTH),
        )

    def mark_reviewed(self) -> "SourceFragment":
        return SourceFragment(
            id=self.id,
            source_version_id=self.source_version_id,
            review_status=FragmentReviewStatus.REVIEWED,
            locator_text=self.locator_text,
            external_url=self.external_url,
        )
