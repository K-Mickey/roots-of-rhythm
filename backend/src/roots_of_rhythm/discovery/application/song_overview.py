from asyncio import gather
from collections.abc import Callable, Collection
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from roots_of_rhythm.discovery.application.dto import (
    ExternalIdentityView,
    GenreSummary,
    LyricsVersionRelationView,
    LyricsVersionSummary,
    PerformerSummary,
    RelatedWorkView,
    SongLyricsVersionView,
    SongOverviewResponse,
    SongPeriodView,
    SongSummary,
    SongWorkCreditView,
    TemporalBoundView,
)
from roots_of_rhythm.discovery.application.errors import SongOverviewNotFound

if TYPE_CHECKING:
    from uuid import UUID

    from roots_of_rhythm.music_catalog.application.lyrics_body_projection import LyricsBodyDisclosure
    from roots_of_rhythm.music_catalog.application.lyrics_version_projection_service import (
        LyricsVersionProjectionService,
    )
    from roots_of_rhythm.music_catalog.application.ports import MusicCatalogUnitOfWork
    from roots_of_rhythm.music_catalog.domain import (
        LyricsVersion,
        LyricsVersionCredit,
        LyricsVersionRelation,
        WorkCredit,
    )
    from roots_of_rhythm.music_catalog.domain.value_objects import ExistencePeriod, TemporalBound
    from roots_of_rhythm.people_catalog.application.ports import PeopleCatalogUnitOfWork
    from roots_of_rhythm.people_catalog.domain import Person

type PeopleUnitOfWorkFactory = Callable[[], PeopleCatalogUnitOfWork]
type MusicUnitOfWorkFactory = Callable[[], MusicCatalogUnitOfWork]


@runtime_checkable
class SongOverviewReader(Protocol):
    async def get(self, song_id: UUID) -> SongOverviewResponse: ...


class SongOverviewQuery:
    def __init__(
        self,
        music_uow_factory: MusicUnitOfWorkFactory,
        people_uow_factory: PeopleUnitOfWorkFactory,
        lyrics_projection: LyricsVersionProjectionService,
    ) -> None:
        self._music_uow_factory = music_uow_factory
        self._people_uow_factory = people_uow_factory
        self._lyrics_projection = lyrics_projection

    async def get(self, song_id: UUID) -> SongOverviewResponse:
        async with self._music_uow_factory() as music_uow:
            work = await music_uow.works.get_published(song_id)
            if work is None:
                raise SongOverviewNotFound(str(song_id))
            work_credits = await music_uow.work_credits.list_published_for_work(song_id)
            assignments = await music_uow.assignments.list_published_for_work(song_id)
            genres = await music_uow.genres.get_published_by_ids(
                [assignment.concept_id for assignment in assignments],
            )
            work_relations = await music_uow.work_relations.list_published_for_work(song_id)
            lyrics_versions = await music_uow.lyrics_versions.list_published_for_work(song_id)
            version_ids = [version.id for version in lyrics_versions]
            lyrics_credits_by_version = await music_uow.lyrics_version_credits.list_published_for_versions(
                version_ids,
            )
            lyrics_relations_by_version = await music_uow.lyrics_version_relations.list_published_for_versions(
                version_ids,
            )
            outbound_relations = [relation for relation in work_relations if relation.source_work_id == song_id]
            related_works = await music_uow.works.get_published_by_ids(
                [relation.target_work_id for relation in outbound_relations],
            )
            other_lyrics_ids = {
                _other_lyrics_version_id(relation, version.id)
                for version in lyrics_versions
                for relation in lyrics_relations_by_version.get(version.id, ())
            } - set(version_ids)
            related_lyrics_versions = {
                version.id: version for version in lyrics_versions
            } | await music_uow.lyrics_versions.get_published_by_ids(other_lyrics_ids)

        person_ids = {credit.person_id for credit in work_credits}
        for version_credits in lyrics_credits_by_version.values():
            person_ids.update(credit.person_id for credit in version_credits)

        persons, body_disclosures = await gather(
            self._load_persons(person_ids),
            self._disclose_lyrics_bodies(lyrics_versions),
        )

        return SongOverviewResponse(
            id=str(work.id),
            name=work.canonical_title,
            aliases=list(work.aliases),
            description=work.description,
            period=_period_view(work.period),
            external_identities=[
                ExternalIdentityView(
                    provider=identity.provider,
                    identifier=identity.identifier,
                    url=identity.url,
                )
                for identity in work.external_identities
            ],
            credits=_work_credit_views(work_credits, persons),
            classifications=sorted(
                (GenreSummary(id=str(genre.id), name=genre.content.canonical_name) for genre in genres.values()),
                key=lambda item: item.name,
            ),
            related_works=sorted(
                (
                    RelatedWorkView(
                        relation_type=relation.relation_type,
                        work=SongSummary(
                            id=str(related_works[relation.target_work_id].id),
                            name=related_works[relation.target_work_id].canonical_title,
                        ),
                    )
                    for relation in outbound_relations
                    if relation.target_work_id in related_works
                ),
                key=lambda item: (item.work.name, item.relation_type.value),
            ),
            lyrics_versions=[
                SongLyricsVersionView(
                    id=str(version.id),
                    language_tag=version.language_tag,
                    label=version.label,
                    usage_kind=version.usage_kind,
                    creation_method=version.creation_method,
                    body=disclosure.body,
                    body_unavailable_reason=disclosure.body_unavailable_reason,
                    credits=_work_credit_views(lyrics_credits_by_version.get(version.id, ()), persons),
                    relations=_lyrics_relation_views(
                        version.id,
                        lyrics_relations_by_version.get(version.id, ()),
                        related_lyrics_versions,
                    ),
                )
                for version, disclosure in zip(lyrics_versions, body_disclosures, strict=True)
            ],
        )

    async def _load_persons(self, person_ids: Collection[UUID]) -> dict[UUID, Person]:
        if not person_ids:
            return {}
        async with self._people_uow_factory() as people_uow:
            return await people_uow.persons.get_published_by_ids(person_ids)

    async def _disclose_lyrics_bodies(self, versions: list[LyricsVersion]) -> list[LyricsBodyDisclosure]:
        return await self._lyrics_projection.disclose_bodies_for_versions(versions)


def _work_credit_views(
    source_credits: Collection[WorkCredit] | Collection[LyricsVersionCredit],
    persons: dict[UUID, Person],
) -> list[SongWorkCreditView]:
    views: list[SongWorkCreditView] = []
    for credit in source_credits:
        person = persons.get(credit.person_id)
        if person is None:
            continue
        views.append(
            SongWorkCreditView(
                person=PerformerSummary(id=str(person.id), name=person.canonical_name),
                role=credit.role,
                credited_as=credit.credited_as,
            ),
        )
    views.sort(key=lambda item: (item.role.value, item.person.name))
    return views


def _lyrics_relation_views(
    version_id: UUID,
    relations: Collection[LyricsVersionRelation],
    versions: dict[UUID, LyricsVersion],
) -> list[LyricsVersionRelationView]:
    views: list[LyricsVersionRelationView] = []
    for relation in relations:
        other_id = _other_lyrics_version_id(relation, version_id)
        other_version = versions.get(other_id)
        if other_version is None:
            continue
        views.append(
            LyricsVersionRelationView(
                relation_type=relation.relation_type,
                version=LyricsVersionSummary(
                    id=str(other_version.id),
                    language_tag=other_version.language_tag,
                    label=other_version.label,
                ),
            ),
        )
    views.sort(key=lambda item: (item.relation_type.value, item.version.language_tag, item.version.label or ""))
    return views


def _other_lyrics_version_id(relation: LyricsVersionRelation, version_id: UUID) -> UUID:
    if relation.source_lyrics_version_id == version_id:
        return relation.target_lyrics_version_id
    return relation.source_lyrics_version_id


def _period_view(period: ExistencePeriod | None) -> SongPeriodView:
    if period is None:
        return SongPeriodView(start=None, end=None)
    return SongPeriodView(
        start=_bound_view(period.start),
        end=_bound_view(period.end),
    )


def _bound_view(bound: TemporalBound | None) -> TemporalBoundView | None:
    if bound is None:
        return None
    return TemporalBoundView(year=bound.year, precision=bound.precision)
