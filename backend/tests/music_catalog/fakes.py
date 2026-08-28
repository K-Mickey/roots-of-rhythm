from typing import TYPE_CHECKING, Self

from roots_of_rhythm.music_catalog.domain import EditorialStatus, LyricsUsageKind

if TYPE_CHECKING:
    from collections.abc import Collection
    from types import TracebackType
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.ports import (
        ClassificationAssignmentRepository,
        GenreRepository,
        GroupMembershipRepository,
        GroupRepository,
        LyricsVersionCreditRepository,
        LyricsVersionRelationRepository,
        LyricsVersionRepository,
        MusicalWorkRepository,
        RecordingRepository,
        WorkCreditRepository,
        WorkRelationRepository,
    )
    from roots_of_rhythm.music_catalog.domain import (
        ClassificationAssignment,
        Genre,
        Group,
        GroupMembership,
        LyricsVersion,
        LyricsVersionCredit,
        LyricsVersionRelation,
        MusicalWork,
        Recording,
        WorkCredit,
        WorkRelation,
    )


class FakeClassificationAssignmentRepository:
    def __init__(self, assignments: dict[UUID, ClassificationAssignment]) -> None:
        self._assignments = assignments

    async def add(self, assignment: ClassificationAssignment) -> None:
        self._assignments[assignment.id] = assignment

    async def get(self, assignment_id: UUID, *, for_update: bool = False) -> ClassificationAssignment | None:
        return self._assignments.get(assignment_id)

    async def list_published_for_person(self, person_id: UUID) -> list[ClassificationAssignment]:
        from roots_of_rhythm.music_catalog.domain import ClassificationTargetKind

        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.target_kind is ClassificationTargetKind.PERSON
            and assignment.target_id == person_id
            and assignment.editorial_status is EditorialStatus.PUBLISHED
        ]

    async def list_published_for_group(self, group_id: UUID) -> list[ClassificationAssignment]:
        from roots_of_rhythm.music_catalog.domain import ClassificationTargetKind

        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.target_kind is ClassificationTargetKind.GROUP
            and assignment.target_id == group_id
            and assignment.editorial_status is EditorialStatus.PUBLISHED
        ]

    async def list_published_for_work(self, work_id: UUID) -> list[ClassificationAssignment]:
        from roots_of_rhythm.music_catalog.domain import ClassificationTargetKind

        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.target_kind is ClassificationTargetKind.MUSICAL_WORK
            and assignment.target_id == work_id
            and assignment.editorial_status is EditorialStatus.PUBLISHED
        ]

    async def list_published_for_recording(self, recording_id: UUID) -> list[ClassificationAssignment]:
        from roots_of_rhythm.music_catalog.domain import ClassificationTargetKind

        return [
            assignment
            for assignment in self._assignments.values()
            if assignment.target_kind is ClassificationTargetKind.RECORDING
            and assignment.target_id == recording_id
            and assignment.editorial_status is EditorialStatus.PUBLISHED
        ]

    async def save(self, assignment: ClassificationAssignment) -> None:
        if assignment.id not in self._assignments:
            raise LookupError(str(assignment.id))
        self._assignments[assignment.id] = assignment


class FakeGenreRepository:
    def __init__(self, genres: dict[UUID, Genre]) -> None:
        self._genres = genres

    async def add(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def get(self, genre_id: UUID, *, for_update: bool = False) -> Genre | None:
        return self._genres.get(genre_id)

    async def get_published(self, genre_id: UUID, *, for_update: bool = False) -> Genre | None:
        genre = self._genres.get(genre_id)
        return genre if genre is not None and genre.editorial_status is EditorialStatus.PUBLISHED else None

    async def get_published_by_ids(self, genre_ids: Collection[UUID]) -> dict[UUID, Genre]:
        return {
            genre_id: genre
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.editorial_status is EditorialStatus.PUBLISHED
        }

    async def list_published(self) -> list[Genre]:
        return sorted(
            (genre for genre in self._genres.values() if genre.editorial_status is EditorialStatus.PUBLISHED),
            key=lambda genre: genre.content.canonical_name,
        )

    async def save(self, genre: Genre) -> None:
        self._genres[genre.id] = genre

    async def mark_deleted(self, genre_id: UUID) -> None:
        self._genres.pop(genre_id, None)

    async def published_among(self, genre_ids: Collection[UUID]) -> set[UUID]:
        return {
            genre_id
            for genre_id in genre_ids
            if (genre := self._genres.get(genre_id)) is not None and genre.editorial_status is EditorialStatus.PUBLISHED
        }

    async def canonical_name_exists(self, canonical_name: str, *, excluding: UUID | None = None) -> bool:
        return any(
            genre.id != excluding and genre.content.canonical_name.lower() == canonical_name.lower()
            for genre in self._genres.values()
        )


class FakeGroupRepository:
    def __init__(self, groups: dict[UUID, Group]) -> None:
        self._groups = groups

    async def add(self, group: Group) -> None:
        self._groups[group.id] = group

    async def get(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        return self._groups.get(group_id)

    async def get_published(self, group_id: UUID, *, for_update: bool = False) -> Group | None:
        group = self._groups.get(group_id)
        return group if group is not None and group.editorial_status is EditorialStatus.PUBLISHED else None

    async def get_published_by_ids(self, group_ids: Collection[UUID]) -> dict[UUID, Group]:
        return {
            group_id: group
            for group_id in set(group_ids)
            if (group := self._groups.get(group_id)) is not None
            and group.editorial_status is EditorialStatus.PUBLISHED
        }

    async def list_published(self) -> list[Group]:
        return sorted(
            (group for group in self._groups.values() if group.editorial_status is EditorialStatus.PUBLISHED),
            key=lambda group: group.canonical_name,
        )

    async def save(self, group: Group) -> None:
        if group.id not in self._groups:
            raise LookupError(str(group.id))
        self._groups[group.id] = group

    async def mark_deleted(self, group_id: UUID) -> None:
        self._groups.pop(group_id, None)


class FakeGroupMembershipRepository:
    def __init__(self, memberships: dict[UUID, GroupMembership]) -> None:
        self._memberships = memberships

    async def add(self, membership: GroupMembership) -> None:
        self._memberships[membership.id] = membership

    async def get(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        return self._memberships.get(membership_id)

    async def get_published(self, membership_id: UUID, *, for_update: bool = False) -> GroupMembership | None:
        membership = self._memberships.get(membership_id)
        if membership is None or membership.editorial_status is not EditorialStatus.PUBLISHED:
            return None
        return membership

    async def list_published_by_group(self, group_id: UUID) -> list[GroupMembership]:
        return sorted(
            (
                membership
                for membership in self._memberships.values()
                if membership.group_id == group_id and membership.editorial_status is EditorialStatus.PUBLISHED
            ),
            key=lambda membership: membership.id,
        )

    async def save(self, membership: GroupMembership) -> None:
        if membership.id not in self._memberships:
            raise LookupError(str(membership.id))
        self._memberships[membership.id] = membership

    async def mark_deleted(self, membership_id: UUID) -> None:
        self._memberships.pop(membership_id, None)


class FakeMusicalWorkRepository:
    def __init__(self, works: dict[UUID, MusicalWork]) -> None:
        self._works = works
        self.locked_ids: list[UUID] = []

    async def add(self, work: MusicalWork) -> None:
        self._works[work.id] = work

    async def get(self, work_id: UUID, *, for_update: bool = False) -> MusicalWork | None:
        return self._works.get(work_id)

    async def get_published(self, work_id: UUID, *, for_update: bool = False) -> MusicalWork | None:
        if for_update:
            self.locked_ids.append(work_id)
        work = self._works.get(work_id)
        return work if work is not None and work.editorial_status is EditorialStatus.PUBLISHED else None

    async def get_published_by_ids(self, work_ids: Collection[UUID]) -> dict[UUID, MusicalWork]:
        return {
            work_id: work
            for work_id in work_ids
            if (work := self._works.get(work_id)) is not None and work.editorial_status is EditorialStatus.PUBLISHED
        }

    async def list_published(self) -> list[MusicalWork]:
        return sorted(
            (work for work in self._works.values() if work.editorial_status is EditorialStatus.PUBLISHED),
            key=lambda work: work.canonical_title,
        )

    async def save(self, work: MusicalWork) -> None:
        if work.id not in self._works:
            raise LookupError(str(work.id))
        self._works[work.id] = work

    async def mark_deleted(self, work_id: UUID) -> None:
        self._works.pop(work_id, None)


class FakeWorkCreditRepository:
    def __init__(self, work_credits: dict[UUID, WorkCredit]) -> None:
        self._credits = work_credits

    async def add(self, credit: WorkCredit) -> None:
        self._credits[credit.id] = credit

    async def get(self, credit_id: UUID, *, for_update: bool = False) -> WorkCredit | None:
        return self._credits.get(credit_id)

    async def get_published(self, credit_id: UUID, *, for_update: bool = False) -> WorkCredit | None:
        credit = self._credits.get(credit_id)
        return credit if credit is not None and credit.editorial_status is EditorialStatus.PUBLISHED else None

    async def list_published_for_work(self, work_id: UUID) -> list[WorkCredit]:
        return sorted(
            (
                credit
                for credit in self._credits.values()
                if credit.work_id == work_id and credit.editorial_status is EditorialStatus.PUBLISHED
            ),
            key=lambda credit: (credit.role.value, credit.id),
        )

    async def save(self, credit: WorkCredit) -> None:
        if credit.id not in self._credits:
            raise LookupError(str(credit.id))
        self._credits[credit.id] = credit

    async def mark_deleted(self, credit_id: UUID) -> None:
        self._credits.pop(credit_id, None)


class FakeWorkRelationRepository:
    def __init__(self, relations: dict[UUID, WorkRelation]) -> None:
        self._relations = relations

    async def add(self, relation: WorkRelation) -> None:
        self._relations[relation.id] = relation

    async def get(self, relation_id: UUID, *, for_update: bool = False) -> WorkRelation | None:
        return self._relations.get(relation_id)

    async def get_published(self, relation_id: UUID, *, for_update: bool = False) -> WorkRelation | None:
        relation = self._relations.get(relation_id)
        if relation is None or relation.editorial_status is not EditorialStatus.PUBLISHED:
            return None
        return relation

    async def list_published_for_work(self, work_id: UUID) -> list[WorkRelation]:
        return sorted(
            (
                relation
                for relation in self._relations.values()
                if relation.editorial_status is EditorialStatus.PUBLISHED
                and (relation.source_work_id == work_id or relation.target_work_id == work_id)
            ),
            key=lambda relation: (relation.relation_type.value, relation.id),
        )

    async def save(self, relation: WorkRelation) -> None:
        if relation.id not in self._relations:
            raise LookupError(str(relation.id))
        self._relations[relation.id] = relation

    async def mark_deleted(self, relation_id: UUID) -> None:
        self._relations.pop(relation_id, None)


class FakeLyricsVersionRepository:
    def __init__(self, versions: dict[UUID, LyricsVersion]) -> None:
        self._versions = versions

    async def add(self, version: LyricsVersion) -> None:
        self._versions[version.id] = version

    async def get(self, version_id: UUID, *, for_update: bool = False) -> LyricsVersion | None:
        return self._versions.get(version_id)

    async def get_published(self, version_id: UUID, *, for_update: bool = False) -> LyricsVersion | None:
        version = self._versions.get(version_id)
        return version if version is not None and version.editorial_status is EditorialStatus.PUBLISHED else None

    async def get_published_by_ids(self, version_ids: Collection[UUID]) -> dict[UUID, LyricsVersion]:
        return {
            version_id: version
            for version_id in version_ids
            if (version := self._versions.get(version_id)) is not None
            and version.editorial_status is EditorialStatus.PUBLISHED
        }

    async def list_published_for_work(self, work_id: UUID) -> list[LyricsVersion]:
        usage_rank = {LyricsUsageKind.PERFORMABLE: 0, LyricsUsageKind.READING_TRANSLATION: 1}
        return sorted(
            (
                version
                for version in self._versions.values()
                if version.work_id == work_id and version.editorial_status is EditorialStatus.PUBLISHED
            ),
            key=lambda version: (
                usage_rank[version.usage_kind],
                version.language_tag,
                version.label or "",
                version.id,
            ),
        )

    async def save(self, version: LyricsVersion) -> None:
        if version.id not in self._versions:
            raise LookupError(str(version.id))
        self._versions[version.id] = version

    async def mark_deleted(self, version_id: UUID) -> None:
        self._versions.pop(version_id, None)


class FakeLyricsVersionCreditRepository:
    def __init__(self, version_credits: dict[UUID, LyricsVersionCredit]) -> None:
        self._credits = version_credits

    async def add(self, credit: LyricsVersionCredit) -> None:
        self._credits[credit.id] = credit

    async def get(self, credit_id: UUID, *, for_update: bool = False) -> LyricsVersionCredit | None:
        return self._credits.get(credit_id)

    async def get_published(self, credit_id: UUID, *, for_update: bool = False) -> LyricsVersionCredit | None:
        credit = self._credits.get(credit_id)
        return credit if credit is not None and credit.editorial_status is EditorialStatus.PUBLISHED else None

    async def list_published_for_version(self, lyrics_version_id: UUID) -> list[LyricsVersionCredit]:
        return sorted(
            (
                credit
                for credit in self._credits.values()
                if credit.lyrics_version_id == lyrics_version_id
                and credit.editorial_status is EditorialStatus.PUBLISHED
            ),
            key=lambda credit: (credit.role.value, credit.id),
        )

    async def list_published_for_versions(
        self,
        lyrics_version_ids: Collection[UUID],
    ) -> dict[UUID, list[LyricsVersionCredit]]:
        ids = set(lyrics_version_ids)
        return {version_id: await self.list_published_for_version(version_id) for version_id in ids}

    async def save(self, credit: LyricsVersionCredit) -> None:
        if credit.id not in self._credits:
            raise LookupError(str(credit.id))
        self._credits[credit.id] = credit

    async def mark_deleted(self, credit_id: UUID) -> None:
        self._credits.pop(credit_id, None)


class FakeLyricsVersionRelationRepository:
    def __init__(self, relations: dict[UUID, LyricsVersionRelation]) -> None:
        self._relations = relations

    async def add(self, relation: LyricsVersionRelation) -> None:
        self._relations[relation.id] = relation

    async def get(self, relation_id: UUID, *, for_update: bool = False) -> LyricsVersionRelation | None:
        return self._relations.get(relation_id)

    async def get_published(self, relation_id: UUID, *, for_update: bool = False) -> LyricsVersionRelation | None:
        relation = self._relations.get(relation_id)
        if relation is None or relation.editorial_status is not EditorialStatus.PUBLISHED:
            return None
        return relation

    async def list_published_for_version(self, lyrics_version_id: UUID) -> list[LyricsVersionRelation]:
        return sorted(
            (
                relation
                for relation in self._relations.values()
                if relation.editorial_status is EditorialStatus.PUBLISHED
                and (
                    relation.source_lyrics_version_id == lyrics_version_id
                    or relation.target_lyrics_version_id == lyrics_version_id
                )
            ),
            key=lambda relation: (relation.relation_type.value, relation.id),
        )

    async def list_published_for_versions(
        self,
        lyrics_version_ids: Collection[UUID],
    ) -> dict[UUID, list[LyricsVersionRelation]]:
        ids = set(lyrics_version_ids)
        return {version_id: await self.list_published_for_version(version_id) for version_id in ids}

    async def save(self, relation: LyricsVersionRelation) -> None:
        if relation.id not in self._relations:
            raise LookupError(str(relation.id))
        self._relations[relation.id] = relation

    async def mark_deleted(self, relation_id: UUID) -> None:
        self._relations.pop(relation_id, None)


class FakeRecordingRepository:
    def __init__(self, recordings: dict[UUID, Recording]) -> None:
        self._recordings = recordings
        self.locked_ids: list[UUID] = []

    async def add(self, recording: Recording) -> None:
        self._recordings[recording.id] = recording

    async def get(self, recording_id: UUID, *, for_update: bool = False) -> Recording | None:
        if for_update:
            self.locked_ids.append(recording_id)
        return self._recordings.get(recording_id)

    async def get_published(self, recording_id: UUID, *, for_update: bool = False) -> Recording | None:
        recording = await self.get(recording_id, for_update=for_update)
        if recording is None or recording.editorial_status is not EditorialStatus.PUBLISHED:
            return None
        return recording

    async def save(self, recording: Recording) -> None:
        if recording.id not in self._recordings:
            raise LookupError(str(recording.id))
        self._recordings[recording.id] = recording

    async def save_status(self, recording: Recording) -> None:
        if recording.id not in self._recordings:
            raise LookupError(str(recording.id))
        self._recordings[recording.id] = recording

    async def mark_deleted(self, recording_id: UUID) -> None:
        self._recordings.pop(recording_id, None)


class FakeMusicCatalogUnitOfWork:
    def __init__(
        self,
        genres: dict[UUID, Genre],
        assignments: dict[UUID, ClassificationAssignment] | None = None,
        groups: dict[UUID, Group] | None = None,
        group_memberships: dict[UUID, GroupMembership] | None = None,
        works: dict[UUID, MusicalWork] | None = None,
        work_credits: dict[UUID, WorkCredit] | None = None,
        work_relations: dict[UUID, WorkRelation] | None = None,
        lyrics_versions: dict[UUID, LyricsVersion] | None = None,
        lyrics_version_credits: dict[UUID, LyricsVersionCredit] | None = None,
        lyrics_version_relations: dict[UUID, LyricsVersionRelation] | None = None,
        recordings: dict[UUID, Recording] | None = None,
    ) -> None:
        self.genres: GenreRepository = FakeGenreRepository(genres)
        self.assignments: ClassificationAssignmentRepository = FakeClassificationAssignmentRepository(
            {} if assignments is None else assignments
        )
        self.groups: GroupRepository = FakeGroupRepository({} if groups is None else groups)
        self.group_memberships: GroupMembershipRepository = FakeGroupMembershipRepository(
            {} if group_memberships is None else group_memberships
        )
        self.works: MusicalWorkRepository = FakeMusicalWorkRepository({} if works is None else works)
        self.work_credits: WorkCreditRepository = FakeWorkCreditRepository({} if work_credits is None else work_credits)
        self.work_relations: WorkRelationRepository = FakeWorkRelationRepository(
            {} if work_relations is None else work_relations
        )
        self.lyrics_versions: LyricsVersionRepository = FakeLyricsVersionRepository(
            {} if lyrics_versions is None else lyrics_versions
        )
        self.lyrics_version_credits: LyricsVersionCreditRepository = FakeLyricsVersionCreditRepository(
            {} if lyrics_version_credits is None else lyrics_version_credits
        )
        self.lyrics_version_relations: LyricsVersionRelationRepository = FakeLyricsVersionRelationRepository(
            {} if lyrics_version_relations is None else lyrics_version_relations
        )
        self.recordings: RecordingRepository = FakeRecordingRepository({} if recordings is None else recordings)
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollbacks += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
