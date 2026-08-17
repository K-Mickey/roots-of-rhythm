from typing import ClassVar, Self
from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import ClassificationKind, EditorialStatus
from roots_of_rhythm.music_catalog.domain.errors import GenrePublicationError
from roots_of_rhythm.music_catalog.domain.value_objects import ClassificationContent


class ClassificationConcept(msgspec.Struct, frozen=True):
    id: UUID
    content: ClassificationContent
    editorial_status: EditorialStatus = EditorialStatus.DRAFT

    kind: ClassVar[ClassificationKind]


class Genre(ClassificationConcept, frozen=True):
    kind: ClassVar[ClassificationKind] = ClassificationKind.GENRE

    def replace_content(self, content: ClassificationContent) -> Self:
        if self.editorial_status is EditorialStatus.PUBLISHED and content.definition is None:
            raise GenrePublicationError(("definition",))
        return Genre(id=self.id, content=content, editorial_status=self.editorial_status)

    def submit_for_review(self) -> Self:
        return self._with_status(EditorialStatus.IN_REVIEW)

    def publish(self) -> Self:
        missing_fields = ("definition",) if self.content.definition is None else ()
        if missing_fields:
            raise GenrePublicationError(missing_fields)
        return self._with_status(EditorialStatus.PUBLISHED)

    def archive(self) -> Self:
        return self._with_status(EditorialStatus.ARCHIVED)

    def _with_status(self, status: EditorialStatus) -> Self:
        return Genre(id=self.id, content=self.content, editorial_status=status)
