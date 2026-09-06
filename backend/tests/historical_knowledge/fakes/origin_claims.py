from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from roots_of_rhythm.historical_knowledge.domain import RecordingOriginClaim


class StubRecordingOriginClaimRepository:
    def __init__(
        self,
        claims_by_recording: dict[UUID, list[RecordingOriginClaim]] | None = None,
    ) -> None:
        self._claims_by_recording = claims_by_recording or {}

    async def add(self, claim: RecordingOriginClaim) -> None:
        self._claims_by_recording.setdefault(claim.recording_id, []).append(claim)

    async def get(self, claim_id: UUID, *, for_update: bool = False) -> RecordingOriginClaim | None:
        return next(
            (claim for claims in self._claims_by_recording.values() for claim in claims if claim.id == claim_id),
            None,
        )

    async def save(self, claim: RecordingOriginClaim) -> None:
        await self.mark_deleted(claim.id)
        await self.add(claim)

    async def mark_deleted(self, claim_id: UUID) -> None:
        for recording_id, claims in self._claims_by_recording.items():
            self._claims_by_recording[recording_id] = [claim for claim in claims if claim.id != claim_id]

    async def list_supported_published_for_recordings(
        self,
        recording_ids: Collection[UUID],
    ) -> dict[UUID, list[RecordingOriginClaim]]:
        return {
            recording_id: [
                claim
                for claim in self._claims_by_recording.get(recording_id, ())
                if claim.is_published and claim.is_supported
            ]
            for recording_id in recording_ids
        }
