from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select

from roots_of_rhythm.historical_knowledge.domain import (
    EditorialStatus as ClaimEditorialStatus,
)
from roots_of_rhythm.historical_knowledge.domain import (
    EvidenceRole,
    EvidenceStatus,
    FragmentReviewStatus,
    RelationType,
)
from roots_of_rhythm.historical_knowledge.infrastructure.models import (
    ClaimEvidenceReferenceRecord,
    GenreRelationClaimRecord,
    SourceFragmentRecord,
    SourceRecord,
    SourceVersionRecord,
)
from roots_of_rhythm.historical_knowledge.infrastructure.unit_of_work import (
    SqlAlchemyHistoricalKnowledgeUnitOfWork,
)
from roots_of_rhythm.infrastructure.database import create_session_factory
from roots_of_rhythm.music_catalog.domain import ClassificationAssignment
from roots_of_rhythm.music_catalog.domain import EditorialStatus as GenreEditorialStatus
from roots_of_rhythm.music_catalog.infrastructure.models import (
    ClassificationAssignmentRecord,
    ClassificationConceptRecord,
    GroupMembershipRecord,
    GroupRecord,
    LyricsVersionRecord,
    MusicalWorkRecord,
    WorkCreditRecord,
)
from roots_of_rhythm.music_catalog.infrastructure.unit_of_work import SqlAlchemyMusicCatalogUnitOfWork
from roots_of_rhythm.people_catalog.domain import EditorialStatus as PersonEditorialStatus
from roots_of_rhythm.people_catalog.infrastructure.models import PersonRecord
from roots_of_rhythm.people_catalog.infrastructure.unit_of_work import SqlAlchemyPeopleCatalogUnitOfWork
from roots_of_rhythm.seed import CorpusSeedRunner
from roots_of_rhythm.seed import corpus as data

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


async def _counts(
    engine: AsyncEngine,
) -> tuple[int, int, int, int, int, int, int, int, int, int, int, int, int]:
    async with engine.connect() as connection:
        genres = await connection.scalar(select(func.count()).select_from(ClassificationConceptRecord))
        persons = await connection.scalar(select(func.count()).select_from(PersonRecord))
        groups = await connection.scalar(select(func.count()).select_from(GroupRecord))
        memberships = await connection.scalar(select(func.count()).select_from(GroupMembershipRecord))
        assignments = await connection.scalar(select(func.count()).select_from(ClassificationAssignmentRecord))
        claims = await connection.scalar(select(func.count()).select_from(GenreRelationClaimRecord))
        sources = await connection.scalar(select(func.count()).select_from(SourceRecord))
        versions = await connection.scalar(select(func.count()).select_from(SourceVersionRecord))
        fragments = await connection.scalar(select(func.count()).select_from(SourceFragmentRecord))
        evidence = await connection.scalar(select(func.count()).select_from(ClaimEvidenceReferenceRecord))
        works = await connection.scalar(select(func.count()).select_from(MusicalWorkRecord))
        work_credits = await connection.scalar(select(func.count()).select_from(WorkCreditRecord))
        lyrics_versions = await connection.scalar(select(func.count()).select_from(LyricsVersionRecord))
    return (
        int(genres or 0),
        int(persons or 0),
        int(groups or 0),
        int(memberships or 0),
        int(assignments or 0),
        int(claims or 0),
        int(sources or 0),
        int(versions or 0),
        int(fragments or 0),
        int(evidence or 0),
        int(works or 0),
        int(work_credits or 0),
        int(lyrics_versions or 0),
    )


@pytest.mark.asyncio
async def test_corpus_seed_is_idempotent_and_exact(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    runner = CorpusSeedRunner(session_factory)

    await runner.run()
    first = await _counts(engine)
    await runner.run()
    second = await _counts(engine)

    assert first == second == (3, 10, 4, 4, 11, 2, 2, 2, 4, 4, 6, 7, 0)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        published_works = await uow.works.list_published()
        work_credits = [await uow.work_credits.get(credit_id) for credit_id, *_ in data.SEED_WORK_CREDITS]

    assert [work.canonical_title for work in published_works] == sorted(
        content.canonical_title for _, content in data.SEED_MUSICAL_WORKS
    )
    assert all(work.editorial_status is GenreEditorialStatus.PUBLISHED for work in published_works)
    assert [
        None if credit is None else (credit.editorial_status, credit.role, credit.credited_as, credit.provenance)
        for credit in work_credits
    ] == [
        (GenreEditorialStatus.PUBLISHED, role, credited_as, data.SEED_ASSIGNMENT_PROVENANCE)
        for _, _, _, role, credited_as in data.SEED_WORK_CREDITS
    ]

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        jazz = await uow.genres.get_published(data.JAZZ_ID)
        swing = await uow.genres.get_published(data.SWING_ID)
        jump = await uow.genres.get_published(data.JUMP_BLUES_ID)

    assert jazz is not None and jazz.content.canonical_name == "Jazz"
    assert swing is not None and swing.content.canonical_name == "Swing"
    assert jump is not None and jump.content.canonical_name == "Jump Blues"
    assert {jazz.editorial_status, swing.editorial_status, jump.editorial_status} == {GenreEditorialStatus.PUBLISHED}

    async with SqlAlchemyPeopleCatalogUnitOfWork(session_factory) as uow:
        persons = [
            await uow.persons.get_published(person_id)
            for person_id, _ in (*data.SEED_PERFORMERS, *data.SEED_SONG_AUTHORS)
        ]
    assert [person.canonical_name for person in persons if person is not None] == [
        name for _, name in (*data.SEED_PERFORMERS, *data.SEED_SONG_AUTHORS)
    ]
    assert all(person is not None and person.editorial_status is PersonEditorialStatus.PUBLISHED for person in persons)

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        person_assignments = [
            await uow.assignments.get(assignment_id) for assignment_id, *_ in data.SEED_PERSON_GENRE_ASSIGNMENTS
        ]
        group_assignments = [
            await uow.assignments.get(assignment_id) for assignment_id, *_ in data.SEED_GROUP_GENRE_ASSIGNMENTS
        ]
        groups = [await uow.groups.get_published(group_id) for group_id, _ in data.SEED_GROUPS]
    assert [
        None if assignment is None else (assignment.editorial_status, assignment.explanation, assignment.provenance)
        for assignment in person_assignments
    ] == [
        (GenreEditorialStatus.PUBLISHED, explanation, provenance)
        for _, _, _, explanation, provenance in data.SEED_PERSON_GENRE_ASSIGNMENTS
    ]
    assert [
        None if assignment is None else (assignment.editorial_status, assignment.explanation, assignment.provenance)
        for assignment in group_assignments
    ] == [
        (GenreEditorialStatus.PUBLISHED, explanation, provenance)
        for _, _, _, explanation, provenance in data.SEED_GROUP_GENRE_ASSIGNMENTS
    ]
    assert [group.canonical_name for group in groups if group is not None] == [
        content.canonical_name for _, content in data.SEED_GROUPS
    ]

    async with SqlAlchemyHistoricalKnowledgeUnitOfWork(session_factory) as uow:
        developed = await uow.claims.get(data.SWING_FROM_JAZZ_CLAIM_ID)
        contributed = await uow.claims.get(data.SWING_TO_JUMP_CLAIM_ID)
        smithsonian = await uow.sources.get_source(data.SMITHSONIAN_SOURCE_ID)
        loc = await uow.sources.get_source(data.LOC_SOURCE_ID)
        fragments = [
            await uow.sources.get_fragment(data.JAZZ_INTRO_FRAGMENT_ID),
            await uow.sources.get_fragment(data.JAZZ_BLUES_FRAGMENT_ID),
            await uow.sources.get_fragment(data.FOLKLIFE_RNB_FRAGMENT_ID),
            await uow.sources.get_fragment(data.LOC_RNB_FRAGMENT_ID),
        ]

    assert developed is not None
    assert developed.editorial_status is ClaimEditorialStatus.PUBLISHED
    assert developed.evidence_status is EvidenceStatus.SUPPORTED
    assert developed.relation_type is RelationType.DEVELOPED_FROM
    assert developed.subject_genre_id == data.SWING_ID
    assert developed.target_genre_id == data.JAZZ_ID
    assert all(ref.role is EvidenceRole.SUPPORTS for ref in developed.evidence_references)
    assert len(developed.evidence_references) == 2

    assert contributed is not None
    assert contributed.editorial_status is ClaimEditorialStatus.PUBLISHED
    assert contributed.evidence_status is EvidenceStatus.SUPPORTED
    assert contributed.relation_type is RelationType.CONTRIBUTED_TO_EMERGENCE_OF
    assert contributed.subject_genre_id == data.SWING_ID
    assert contributed.target_genre_id == data.JUMP_BLUES_ID
    assert len(contributed.evidence_references) == 2

    assert smithsonian is not None and smithsonian.title == data.SMITHSONIAN_TITLE
    assert smithsonian.responsible_organization == data.SMITHSONIAN_RESPONSIBLE_ORGANIZATION
    assert smithsonian.external_url == data.SMITHSONIAN_EXTERNAL_URL
    assert smithsonian.author is None
    assert smithsonian.publication is None
    assert smithsonian.publication_date is None
    assert loc is not None and loc.title == data.LOC_TITLE
    assert loc.responsible_organization == data.LOC_RESPONSIBLE_ORGANIZATION
    assert loc.external_url == data.LOC_EXTERNAL_URL
    assert loc.author is None
    assert loc.publication is None
    assert loc.publication_date is None
    assert all(
        fragment is not None and fragment.review_status is FragmentReviewStatus.REVIEWED for fragment in fragments
    )

    # Controlled corpus still has no separate Performer table; Recording seed is STORY-008 TASK-007.
    async with engine.connect() as connection:
        tables = set(await connection.run_sync(lambda sync: sync.dialect.get_table_names(sync)))
    assert "performers" not in tables
    assert {
        "groups",
        "group_memberships",
        "musical_works",
        "work_credits",
        "recordings",
        "recording_credits",
        "recording_work_usages",
    } <= tables
    assert "lyrics_versions" in tables


@pytest.mark.asyncio
async def test_corpus_seed_repairs_published_assignment_content(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    runner = CorpusSeedRunner(session_factory)
    await runner.run()
    assignment_id, _, _, explanation, provenance = data.SEED_PERSON_GENRE_ASSIGNMENTS[0]
    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        assignment = await uow.assignments.get(assignment_id)
        assert assignment is not None
        await uow.assignments.save(
            ClassificationAssignment(
                id=assignment.id,
                target_kind=assignment.target_kind,
                target_id=assignment.target_id,
                concept_id=assignment.concept_id,
                editorial_status=assignment.editorial_status,
            )
        )
        await uow.commit()

    await runner.run()

    async with SqlAlchemyMusicCatalogUnitOfWork(session_factory) as uow:
        repaired = await uow.assignments.get(assignment_id)
    assert repaired is not None
    assert repaired.explanation == explanation
    assert repaired.provenance == provenance
    assert repaired.editorial_status is GenreEditorialStatus.PUBLISHED
