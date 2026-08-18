"""Controlled Genre corpus seed data (Jazz, Swing, Jump Blues).

Stable identities are fixed UUID7 literals. Re-running seed is a no-op for existing rows
and never invents Performer/Group/Recording entities.
"""

from uuid import UUID

from roots_of_rhythm.historical_knowledge.domain import (
    ClaimEvidenceReference,
    ClaimProvenance,
    EvidenceRole,
    EvidenceStatus,
    GeographicContext,
    HistoricalPeriod,
    RelationType,
    TemporalBound,
    TemporalPrecision,
)
from roots_of_rhythm.music_catalog.domain import ClassificationContent

# --- Genres -----------------------------------------------------------------
JAZZ_ID = UUID("01a0147a-8508-74b7-9689-e7c079b95327")
SWING_ID = UUID("01a0147a-8508-74b7-9689-e7c133e4e7a5")
JUMP_BLUES_ID = UUID("01a0147a-8508-74b7-9689-e7c272039bac")

JAZZ_CONTENT = ClassificationContent.create(
    "Jazz",
    definition=(
        "Американская музыкальная традиция, выросшая в афроамериканских сообществах: "
        "от раннего jazz через big bands эпохи Swing Era к более поздним стилям."
    ),
)
SWING_CONTENT = ClassificationContent.create(
    "Swing",
    definition=(
        "Стиль Jazz эпохи Swing Era: оркестровые аранжировки big band, танцевальный ритм и импровизирующие солисты."
    ),
)
JUMP_BLUES_CONTENT = ClassificationContent.create(
    "Jump Blues",
    definition=(
        "Компактный послевоенный стиль: swing-ритм и духовые riffs "
        "в соединении с Blues, shuffle и линиями Boogie-Woogie bass."
    ),
)

# --- Sources ----------------------------------------------------------------
SMITHSONIAN_SOURCE_ID = UUID("01a0147a-8508-74b7-9689-e7c3052e0e19")
SMITHSONIAN_VERSION_ID = UUID("01a0147a-8508-74b7-9689-e7c4d86d78f9")
LOC_SOURCE_ID = UUID("01a0147a-8508-74b7-9689-e7c58c0b7736")
LOC_VERSION_ID = UUID("01a0147a-8508-74b7-9689-e7c6043bca04")

SMITHSONIAN_TITLE = "Smithsonian Music"
SMITHSONIAN_INSTITUTION = "Smithsonian"
LOC_TITLE = "Library of Congress"
LOC_INSTITUTION = "Library of Congress"
SOURCE_VERSION_LABEL = "web 2026-08"

# --- Fragments --------------------------------------------------------------
JAZZ_INTRO_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7c7f9e6dc36")
JAZZ_BLUES_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7c8cd1c114b")
FOLKLIFE_RNB_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7c95d709c45")
LOC_RNB_FRAGMENT_ID = UUID("01a0147a-8508-74b7-9689-e7ca7a660b98")

JAZZ_INTRO_URL = "https://music.si.edu/story/jazz"
JAZZ_BLUES_URL = "https://music.si.edu/spotlight/african-american-music/jazz-blues"
FOLKLIFE_RNB_URL = "https://folklife.si.edu/magazine/freedom-sounds-tell-it-like-it-is-a-history-of-rhythm-and-blues"
LOC_RNB_URL = (
    "https://www.loc.gov/collections/songs-of-america/articles-and-essays/"
    "musical-styles/popular-songs-of-the-day/rhythm-and-blues/"
)

# --- Claims -----------------------------------------------------------------
SWING_FROM_JAZZ_CLAIM_ID = UUID("01a0147a-8508-74b7-9689-e7cb0316a0f5")
SWING_TO_JUMP_CLAIM_ID = UUID("01a0147a-8508-74b7-9689-e7cc2797195b")

SWING_FROM_JAZZ_EXPLANATION = (
    "Swing сформировался внутри американской джазовой традиции на основе развития "
    "оркестровых аранжировок, ритмической организации и роли импровизирующих солистов. "
    "В 1930-е эти изменения оформились в Swing Era и сделали большие джазовые оркестры "
    "центральной частью массовой танцевальной культуры."
)
SWING_TO_JUMP_EXPLANATION = (
    "Swing был одним из основных входов в формирование Jump Blues. Музыканты перенесли "
    "swing-ритм, духовые riffs и опыт больших оркестров в более компактные составы, "
    "соединив их с Blues, shuffle rhythm и Boogie-Woogie bass lines. Поэтому Jump Blues "
    "нельзя описывать как продолжение только одного Swing."
)

SWING_FROM_JAZZ_TEMPORAL = HistoricalPeriod.create(
    "late 1920s–1930s",
    TemporalBound(1920, TemporalPrecision.LATE_DECADE),
    TemporalBound(1930, TemporalPrecision.DECADE),
)
SWING_TO_JUMP_TEMPORAL = HistoricalPeriod.create(
    "late 1930s–1940s",
    TemporalBound(1930, TemporalPrecision.LATE_DECADE),
    TemporalBound(1940, TemporalPrecision.DECADE),
)

SWING_FROM_JAZZ_GEOGRAPHIC = GeographicContext.create("United States")
SWING_TO_JUMP_GEOGRAPHIC = GeographicContext.create(
    "United States urban African American music scenes",
)

SWING_FROM_JAZZ_PROVENANCE = ClaimProvenance.create(
    "Редакционный синтез материалов Smithsonian Music о Jazz для controlled corpus seed.",
)
SWING_TO_JUMP_PROVENANCE = ClaimProvenance.create(
    "Редакционный синтез Smithsonian Folklife и Library of Congress о Rhythm and Blues для controlled corpus seed.",
)

SWING_FROM_JAZZ_EVIDENCE = (
    ClaimEvidenceReference.create(
        JAZZ_INTRO_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="От Jazz Age к Swing Era",
        external_url=JAZZ_INTRO_URL,
    ),
    ClaimEvidenceReference.create(
        JAZZ_BLUES_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Big bands Swing Era 1930-х",
        external_url=JAZZ_BLUES_URL,
    ),
)
SWING_TO_JUMP_EVIDENCE = (
    ClaimEvidenceReference.create(
        FOLKLIFE_RNB_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Jump Blues как смесь Swing и Blues",
        external_url=FOLKLIFE_RNB_URL,
    ),
    ClaimEvidenceReference.create(
        LOC_RNB_FRAGMENT_ID,
        EvidenceRole.SUPPORTS,
        locator_text="Ранний R&B и афроамериканский Swing",
        external_url=LOC_RNB_URL,
    ),
)

SWING_FROM_JAZZ_RELATION = RelationType.DEVELOPED_FROM
SWING_TO_JUMP_RELATION = RelationType.CONTRIBUTED_TO_EMERGENCE_OF
SWING_FROM_JAZZ_EVIDENCE_STATUS = EvidenceStatus.SUPPORTED
SWING_TO_JUMP_EVIDENCE_STATUS = EvidenceStatus.SUPPORTED
