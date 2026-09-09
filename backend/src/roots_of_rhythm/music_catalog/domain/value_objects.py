from uuid import UUID

import msgspec

from roots_of_rhythm.music_catalog.domain.enums import (
    BillingRole,
    LyricsCreationMethod,
    LyricsUsageKind,
    LyricsVersionRelationType,
    RecordingContributionKind,
    RecordingCreditTargetKind,
    RecordingWorkUsageKind,
    TemporalPrecision,
    WorkCreditRole,
    WorkRelationType,
)
from roots_of_rhythm.music_catalog.domain.errors import LyricsVersionInvalidCombinationError, MusicCatalogDomainError
from roots_of_rhythm.utils.language import canonicalize_language_tag, normalize_isrc
from roots_of_rhythm.utils.text import (
    is_http_url,
    optional_body_text,
    optional_text,
    required_text,
    unique_texts,
)
from roots_of_rhythm.utils.text_lengths import TEXT_64, TEXT_1024, TEXT_2048, TEXT_4096

_CREDITED_AS_FIELD = "credited as"


class TemporalBound(msgspec.Struct, frozen=True):
    year: int
    precision: TemporalPrecision


class ExistencePeriod(msgspec.Struct, frozen=True):
    start: TemporalBound | None = None
    end: TemporalBound | None = None

    @classmethod
    def create(
        cls,
        start: TemporalBound | None = None,
        end: TemporalBound | None = None,
    ) -> "ExistencePeriod":
        if start is not None and end is not None and start.year > end.year:
            raise MusicCatalogDomainError("period start must not be later than period end")
        return cls(start=start, end=end)


class HistoricalPeriod(msgspec.Struct, frozen=True):
    label: str
    start: TemporalBound | None = None
    end: TemporalBound | None = None

    @classmethod
    def create(
        cls,
        label: str,
        start: TemporalBound | None = None,
        end: TemporalBound | None = None,
    ) -> "HistoricalPeriod":
        if start is not None and end is not None and start.year > end.year:
            raise MusicCatalogDomainError("period start must not be later than period end")
        return cls(
            label=required_text(label, "period label", max_length=TEXT_64, error=MusicCatalogDomainError),
            start=start,
            end=end,
        )


class GeographicContext(msgspec.Struct, frozen=True):
    summary: str

    @classmethod
    def create(cls, summary: str) -> "GeographicContext":
        return cls(
            summary=required_text(summary, "geographic summary", max_length=TEXT_64, error=MusicCatalogDomainError)
        )


class ClassificationContent(msgspec.Struct, frozen=True):
    canonical_name: str
    aliases: tuple[str, ...] = ()
    definition: str | None = None
    boundaries: str | None = None
    period: HistoricalPeriod | None = None
    geography: GeographicContext | None = None
    historical_context: str | None = None
    formation: str | None = None
    characteristic_features: tuple[str, ...] = ()
    primary_image_id: UUID | None = None

    @classmethod
    def create(
        cls,
        canonical_name: str,
        *,
        aliases: tuple[str, ...] = (),
        definition: str | None = None,
        boundaries: str | None = None,
        period: HistoricalPeriod | None = None,
        geography: GeographicContext | None = None,
        historical_context: str | None = None,
        formation: str | None = None,
        characteristic_features: tuple[str, ...] = (),
        primary_image_id: UUID | None = None,
    ) -> "ClassificationContent":
        normalized_name = required_text(
            canonical_name,
            "canonical name",
            max_length=TEXT_64,
            error=MusicCatalogDomainError,
        )
        normalized_aliases = unique_texts(aliases, "aliases", max_length=TEXT_64, error=MusicCatalogDomainError)
        if normalized_name.casefold() in {alias.casefold() for alias in normalized_aliases}:
            raise MusicCatalogDomainError("aliases must not duplicate the canonical name")
        return cls(
            canonical_name=normalized_name,
            aliases=normalized_aliases,
            definition=optional_text(definition, "definition", max_length=TEXT_1024, error=MusicCatalogDomainError),
            boundaries=optional_text(boundaries, "boundaries", max_length=TEXT_1024, error=MusicCatalogDomainError),
            period=period,
            geography=geography,
            historical_context=optional_text(
                historical_context,
                "historical context",
                max_length=TEXT_1024,
                error=MusicCatalogDomainError,
            ),
            formation=optional_text(formation, "formation", max_length=TEXT_1024, error=MusicCatalogDomainError),
            characteristic_features=unique_texts(
                characteristic_features,
                "characteristic features",
                max_length=TEXT_64,
                error=MusicCatalogDomainError,
            ),
            primary_image_id=primary_image_id,
        )


class GroupContent(msgspec.Struct, frozen=True):
    canonical_name: str
    aliases: tuple[str, ...] = ()
    description: str | None = None
    period: ExistencePeriod | None = None

    @classmethod
    def create(
        cls,
        canonical_name: str,
        *,
        aliases: tuple[str, ...] = (),
        description: str | None = None,
        period: ExistencePeriod | None = None,
    ) -> "GroupContent":
        normalized_name = required_text(
            canonical_name,
            "canonical name",
            max_length=TEXT_64,
            error=MusicCatalogDomainError,
        )
        normalized_aliases = unique_texts(aliases, "aliases", max_length=TEXT_64, error=MusicCatalogDomainError)
        if normalized_name.casefold() in {alias.casefold() for alias in normalized_aliases}:
            raise MusicCatalogDomainError("aliases must not duplicate the canonical name")
        return cls(
            canonical_name=normalized_name,
            aliases=normalized_aliases,
            description=optional_text(description, "description", max_length=TEXT_1024, error=MusicCatalogDomainError),
            period=period,
        )


class ExternalIdentity(msgspec.Struct, frozen=True):
    provider: str
    identifier: str
    url: str | None = None

    @classmethod
    def create(cls, provider: str, identifier: str, *, url: str | None = None) -> "ExternalIdentity":
        normalized_url = optional_text(
            url, "external identity URL", max_length=TEXT_2048, error=MusicCatalogDomainError
        )
        if normalized_url is not None and not is_http_url(normalized_url):
            raise MusicCatalogDomainError("external identity URL must use http or https")
        return cls(
            provider=required_text(
                provider, "external identity provider", max_length=TEXT_64, error=MusicCatalogDomainError
            ),
            identifier=required_text(
                identifier, "external identity identifier", max_length=TEXT_64, error=MusicCatalogDomainError
            ),
            url=normalized_url,
        )


class WorkContent(msgspec.Struct, frozen=True):
    canonical_title: str
    aliases: tuple[str, ...] = ()
    description: str | None = None
    period: ExistencePeriod | None = None
    external_identities: tuple[ExternalIdentity, ...] = ()
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        canonical_title: str,
        *,
        aliases: tuple[str, ...] = (),
        description: str | None = None,
        period: ExistencePeriod | None = None,
        external_identities: tuple[ExternalIdentity, ...] = (),
        provenance: str | None = None,
    ) -> "WorkContent":
        normalized_title = required_text(
            canonical_title,
            "canonical title",
            max_length=TEXT_64,
            error=MusicCatalogDomainError,
        )
        normalized_aliases = unique_texts(aliases, "aliases", max_length=TEXT_64, error=MusicCatalogDomainError)
        if normalized_title.casefold() in {alias.casefold() for alias in normalized_aliases}:
            raise MusicCatalogDomainError("aliases must not duplicate the canonical title")
        normalized_identities = tuple(
            ExternalIdentity.create(identity.provider, identity.identifier, url=identity.url)
            for identity in external_identities
        )
        identity_keys = tuple(
            (identity.provider.casefold(), identity.identifier.casefold()) for identity in normalized_identities
        )
        if len(identity_keys) != len(set(identity_keys)):
            raise MusicCatalogDomainError("external identities must not contain duplicates")
        return cls(
            canonical_title=normalized_title,
            aliases=normalized_aliases,
            description=optional_text(description, "description", max_length=TEXT_1024, error=MusicCatalogDomainError),
            period=period,
            external_identities=normalized_identities,
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class WorkCreditContent(msgspec.Struct, frozen=True):
    role: WorkCreditRole
    credited_as: str | None = None
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        *,
        role: WorkCreditRole,
        credited_as: str | None = None,
        provenance: str | None = None,
    ) -> "WorkCreditContent":
        return cls(
            role=role,
            credited_as=optional_text(
                credited_as, _CREDITED_AS_FIELD, max_length=TEXT_64, error=MusicCatalogDomainError
            ),
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class WorkRelationContent(msgspec.Struct, frozen=True):
    relation_type: WorkRelationType
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        *,
        relation_type: WorkRelationType,
        provenance: str | None = None,
    ) -> "WorkRelationContent":
        return cls(
            relation_type=relation_type,
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class LyricsVersionContent(msgspec.Struct, frozen=True):
    language_tag: str
    usage_kind: LyricsUsageKind
    creation_method: LyricsCreationMethod
    label: str | None = None
    body: str | None = None
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        *,
        language_tag: str,
        usage_kind: LyricsUsageKind,
        creation_method: LyricsCreationMethod,
        label: str | None = None,
        body: str | None = None,
        provenance: str | None = None,
    ) -> "LyricsVersionContent":
        if creation_method is LyricsCreationMethod.MACHINE_TRANSLATION and usage_kind is LyricsUsageKind.PERFORMABLE:
            raise LyricsVersionInvalidCombinationError()
        return cls(
            language_tag=canonicalize_language_tag(language_tag, error=MusicCatalogDomainError),
            usage_kind=usage_kind,
            creation_method=creation_method,
            label=optional_text(label, "label", max_length=TEXT_64, error=MusicCatalogDomainError),
            body=optional_body_text(body, "body", max_length=TEXT_4096, error=MusicCatalogDomainError),
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class LyricsVersionCreditContent(msgspec.Struct, frozen=True):
    role: WorkCreditRole
    credited_as: str | None = None
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        *,
        role: WorkCreditRole,
        credited_as: str | None = None,
        provenance: str | None = None,
    ) -> "LyricsVersionCreditContent":
        return cls(
            role=role,
            credited_as=optional_text(
                credited_as, _CREDITED_AS_FIELD, max_length=TEXT_64, error=MusicCatalogDomainError
            ),
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class LyricsVersionRelationContent(msgspec.Struct, frozen=True):
    relation_type: LyricsVersionRelationType
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        *,
        relation_type: LyricsVersionRelationType,
        provenance: str | None = None,
    ) -> "LyricsVersionRelationContent":
        return cls(
            relation_type=relation_type,
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class GroupMembershipContent(msgspec.Struct, frozen=True):
    period: ExistencePeriod | None = None
    roles_or_instruments: tuple[str, ...] = ()
    provenance: str | None = None

    @classmethod
    def create(
        cls,
        *,
        period: ExistencePeriod | None = None,
        roles_or_instruments: tuple[str, ...] = (),
        provenance: str | None = None,
    ) -> "GroupMembershipContent":
        return cls(
            period=period,
            roles_or_instruments=unique_texts(
                roles_or_instruments,
                "roles or instruments",
                max_length=TEXT_64,
                error=MusicCatalogDomainError,
            ),
            provenance=optional_text(provenance, "provenance", max_length=TEXT_1024, error=MusicCatalogDomainError),
        )


class RecordingCredit(msgspec.Struct, frozen=True):
    id: UUID
    target_kind: RecordingCreditTargetKind
    target_id: UUID
    billing_role: BillingRole
    contribution_kind: RecordingContributionKind | None = None
    instrument: str | None = None
    credited_as: str | None = None

    @classmethod
    def create(
        cls,
        credit_id: UUID,
        target_kind: RecordingCreditTargetKind,
        target_id: UUID,
        billing_role: BillingRole,
        *,
        contribution_kind: RecordingContributionKind | None = None,
        instrument: str | None = None,
        credited_as: str | None = None,
    ) -> "RecordingCredit":
        return cls(
            id=credit_id,
            target_kind=target_kind,
            target_id=target_id,
            billing_role=billing_role,
            contribution_kind=contribution_kind,
            instrument=optional_text(instrument, "instrument", max_length=TEXT_64, error=MusicCatalogDomainError),
            credited_as=optional_text(
                credited_as, _CREDITED_AS_FIELD, max_length=TEXT_64, error=MusicCatalogDomainError
            ),
        )

    @property
    def is_primary_person(self) -> bool:
        return self.is_primary_billing and self.is_person_target

    @property
    def is_primary_group(self) -> bool:
        return self.is_primary_billing and self.is_group_target

    @property
    def is_primary_billing(self) -> bool:
        return self.billing_role is BillingRole.PRIMARY

    @property
    def is_group_target(self) -> bool:
        return self.target_kind is RecordingCreditTargetKind.GROUP

    @property
    def is_person_target(self) -> bool:
        return self.target_kind is RecordingCreditTargetKind.PERSON


class RecordingWorkUsage(msgspec.Struct, frozen=True):
    id: UUID
    work_id: UUID
    usage_kind: RecordingWorkUsageKind
    position: int | None = None

    @classmethod
    def create(
        cls,
        usage_id: UUID,
        work_id: UUID,
        usage_kind: RecordingWorkUsageKind,
        *,
        position: int | None = None,
    ) -> "RecordingWorkUsage":
        if position is not None and position <= 0:
            raise MusicCatalogDomainError("work usage position must be positive")
        return cls(id=usage_id, work_id=work_id, usage_kind=usage_kind, position=position)

    @property
    def is_complete(self) -> bool:
        return self.usage_kind is RecordingWorkUsageKind.COMPLETE

    @property
    def is_partial(self) -> bool:
        return self.usage_kind is RecordingWorkUsageKind.PARTIAL


class RecordingLyricsUsage(msgspec.Struct, frozen=True):
    id: UUID
    lyrics_version_id: UUID
    position: int = 0

    @classmethod
    def create(cls, usage_id: UUID, lyrics_version_id: UUID) -> "RecordingLyricsUsage":
        return cls(id=usage_id, lyrics_version_id=lyrics_version_id)


class RecordingContent(msgspec.Struct, frozen=True):
    title: str
    recorded_period: ExistencePeriod | None = None
    description: str | None = None
    isrc: str | None = None
    credits: tuple[RecordingCredit, ...] = ()
    work_usages: tuple[RecordingWorkUsage, ...] = ()
    lyrics_usages: tuple[RecordingLyricsUsage, ...] = ()

    @classmethod
    def create(
        cls,
        title: str,
        *,
        recorded_period: ExistencePeriod | None = None,
        description: str | None = None,
        isrc: str | None = None,
        recording_credits: tuple[RecordingCredit, ...] = (),
        work_usages: tuple[RecordingWorkUsage, ...] = (),
        lyrics_usages: tuple[RecordingLyricsUsage, ...] = (),
    ) -> "RecordingContent":
        normalized_isrc = None
        if isrc is not None:
            normalized_isrc = normalize_isrc(isrc, error=MusicCatalogDomainError)

        usage_keys = tuple((usage.work_id, usage.usage_kind) for usage in work_usages)
        if len(usage_keys) != len(set(usage_keys)):
            raise MusicCatalogDomainError("work usages must not contain duplicate work and usage kind")

        usage_kinds = {usage.usage_kind for usage in work_usages}
        if len(usage_kinds) > 1:
            raise MusicCatalogDomainError("work usages must use one usage kind")
        if (
            work_usages
            and next(iter(usage_kinds)) is not RecordingWorkUsageKind.MEDLEY_COMPONENT
            and len(work_usages) > 1
        ):
            raise MusicCatalogDomainError("complete and partial recordings require exactly one work usage")

        medley = tuple(usage for usage in work_usages if usage.usage_kind is RecordingWorkUsageKind.MEDLEY_COMPONENT)
        if len(medley) > 1:
            positions = tuple(usage.position for usage in medley)
            if any(position is None for position in positions):
                raise MusicCatalogDomainError("multiple medley components require positions")
            if len(positions) != len(set(positions)):
                raise MusicCatalogDomainError("medley component positions must be unique")

        lyrics_version_ids = [usage.lyrics_version_id for usage in lyrics_usages]
        if len(lyrics_version_ids) != len(set(lyrics_version_ids)):
            raise MusicCatalogDomainError("lyrics usages must not contain duplicate LyricsVersion")
        ordered_lyrics_usages = tuple(
            RecordingLyricsUsage(id=usage.id, lyrics_version_id=usage.lyrics_version_id, position=position)
            for position, usage in enumerate(lyrics_usages, start=1)
        )

        return cls(
            title=required_text(title, "recording title", max_length=TEXT_64, error=MusicCatalogDomainError),
            recorded_period=recorded_period,
            description=optional_text(description, "description", max_length=TEXT_1024, error=MusicCatalogDomainError),
            isrc=normalized_isrc,
            credits=recording_credits,
            work_usages=work_usages,
            lyrics_usages=ordered_lyrics_usages,
        )
