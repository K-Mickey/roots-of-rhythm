from __future__ import annotations

from typing import TYPE_CHECKING

from roots_of_rhythm.historical_knowledge.domain import SourceAccessPolicy

if TYPE_CHECKING:
    from roots_of_rhythm.music_catalog.domain import LyricsVersion

RIGHTS_RESTRICTED_REASON = "rights_restricted"


class LyricsBodyDisclosure:
    __slots__ = ("body", "body_unavailable_reason")

    def __init__(self, *, body: str | None, body_unavailable_reason: str | None) -> None:
        self.body = body
        self.body_unavailable_reason = body_unavailable_reason


def project_lyrics_version_body(
    version: LyricsVersion,
    access_policy: SourceAccessPolicy | None,
) -> LyricsBodyDisclosure:
    if access_policy is SourceAccessPolicy.ALLOW_PUBLIC_BODY:
        return LyricsBodyDisclosure(body=version.body, body_unavailable_reason=None)
    return LyricsBodyDisclosure(body=None, body_unavailable_reason=RIGHTS_RESTRICTED_REASON)
