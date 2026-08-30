'use client';

import {
  Anchor,
  Badge,
  Box,
  Container,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';

import type { SongOverview } from '@/shared/api/song';
import type { RecordingOverview } from '@/shared/api/recording';
import { RecordingDetails } from '@/features/recording-page/RecordingPageContent';
import { RecordingLyricsSection } from '@/features/recording-page/RecordingLyricsSection';
import { formatOriginBadge } from '@/features/recording-page/labels';

import {
  formatPeriod,
  formatTemporalBound,
  formatWorkCreditRole,
  formatWorkRelationType,
  hasPeriodBounds,
  safeExternalHref,
} from './labels';
import {
  matchesRecordingGenre,
  resolveSongSelection,
  selectionHref,
} from './selection';
import classes from './SongPageContent.module.css';

export function SongPageContent({
  song,
  recording = null,
}: {
  song: SongOverview;
  recording?: RecordingOverview | null;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selection = resolveSongSelection(
    song,
    {
      genre: searchParams.get('genre') ?? undefined,
      recording: searchParams.get('recording') ?? undefined,
      text: searchParams.get('text') ?? undefined,
    },
    recording,
  );
  const canonicalHref = selectionHref(pathname, selection);
  const aliases = song.aliases;
  const identities = song.external_identities;
  const songPeriod = hasPeriodBounds(song.period)
    ? formatPeriod(song.period)
    : null;
  const lyricsVersions = song.lyrics_versions;

  useEffect(() => {
    const current = searchParams.toString();
    const currentHref = current ? `${pathname}?${current}` : pathname;
    if (currentHref !== canonicalHref) {
      router.replace(canonicalHref, { scroll: false });
    }
  }, [canonicalHref, pathname, router, searchParams]);

  return (
    <Container size="72rem" py="xl" style={{ containerType: 'inline-size' }}>
      <Stack gap="xl" component="article">
        <Stack gap="md" component="section">
          <Title order={1}>{song.name}</Title>
          {aliases.length > 0 ? (
            <Text c="pastel.8" size="sm">
              Также известна как: {aliases.join(', ')}
            </Text>
          ) : null}
          {songPeriod !== null ? (
            <Text c="pastel.8" size="sm">
              Период: {songPeriod}
            </Text>
          ) : null}
          {song.description !== null ? <Text>{song.description}</Text> : null}
        </Stack>

        {identities.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="identities-heading"
          >
            <Title order={2} id="identities-heading">
              Внешние идентификаторы
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {identities.map((identity) => {
                const href =
                  identity.url === null ? null : safeExternalHref(identity.url);
                const label = `${identity.provider}: ${identity.identifier}`;

                return (
                  <li key={`${identity.provider}:${identity.identifier}`}>
                    {href !== null ? (
                      <Anchor
                        href={href}
                        c="pastel.7"
                        underline="always"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {label}
                      </Anchor>
                    ) : (
                      <Text>{label}</Text>
                    )}
                  </li>
                );
              })}
            </Stack>
          </Stack>
        ) : null}

        {song.credits.length > 0 ? (
          <Stack gap="sm" component="section" aria-labelledby="authors-heading">
            <Title order={2} id="authors-heading">
              Авторы
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {song.credits.map((credit) => {
                const roleLabel = formatWorkCreditRole(credit.role);
                const creditedAs =
                  credit.credited_as !== null
                    ? ` (как ${credit.credited_as})`
                    : '';

                return (
                  <li
                    key={`${credit.person.id}:${credit.role}:${credit.credited_as ?? ''}`}
                  >
                    <Anchor
                      component={Link}
                      href={`/performers/${encodeURIComponent(credit.person.id)}`}
                      c="pastel.7"
                      underline="always"
                    >
                      {credit.person.name}
                    </Anchor>
                    {creditedAs}
                    {' — '}
                    {roleLabel}
                  </li>
                );
              })}
            </Stack>
          </Stack>
        ) : null}

        {song.classifications.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="classifications-heading"
          >
            <Title order={2} id="classifications-heading">
              Классификация произведения
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {song.classifications.map((genre) => (
                <li key={genre.id}>
                  <Anchor
                    component={Link}
                    href={`/genres/${encodeURIComponent(genre.id)}`}
                    c="pastel.7"
                    underline="always"
                  >
                    {genre.name}
                  </Anchor>
                </li>
              ))}
            </Stack>
          </Stack>
        ) : null}

        {song.related_works.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="related-works-heading"
          >
            <Title order={2} id="related-works-heading">
              Связанные произведения
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {song.related_works.map((related) => (
                <li key={`${related.relation_type}:${related.work.id}`}>
                  {formatWorkRelationType(related.relation_type)}
                  {': '}
                  <Anchor
                    component={Link}
                    href={`/songs/${encodeURIComponent(related.work.id)}`}
                    c="pastel.7"
                    underline="always"
                  >
                    {related.work.name}
                  </Anchor>
                </li>
              ))}
            </Stack>
          </Stack>
        ) : null}

        {selection.recordingId !== null &&
        recording !== null &&
        recording.id === selection.recordingId ? (
          <RecordingStudyArea
            song={song}
            recording={recording}
            selection={selection}
            pathname={pathname}
          />
        ) : lyricsVersions.length > 0 ? (
          <RecordingLyricsSection
            versions={lyricsVersions}
            selectedId={selection.textId}
          />
        ) : null}
      </Stack>
    </Container>
  );
}

function RecordingStudyArea({
  song,
  recording,
  selection,
  pathname,
}: {
  song: SongOverview;
  recording: RecordingOverview;
  selection: ReturnType<typeof resolveSongSelection>;
  pathname: string;
}) {
  const hasChronology = song.recordings.length > 1;
  const summary = song.recordings.find(
    (item) => item.id === selection.recordingId,
  );
  const chronology = (
    <RecordingChronology
      song={song}
      selection={selection}
      pathname={pathname}
    />
  );

  return (
    <div className={hasChronology ? classes.recordingsGrid : undefined}>
      {hasChronology ? (
        <aside className={classes.timeline}>{chronology}</aside>
      ) : null}
      <Box className={classes.recordingContent}>
        <RecordingDetails
          recording={recording}
          headingOrder={2}
          excludeWorkId={song.id}
          lyricsSelectedId={selection.textId}
          originBadges={summary?.origin_badges ?? []}
        />
      </Box>
    </div>
  );
}

function RecordingChronology({
  song,
  selection,
  pathname,
}: {
  song: SongOverview;
  selection: ReturnType<typeof resolveSongSelection>;
  pathname: string;
}) {
  const groups = new Map<string, SongOverview['recordings']>();
  for (const item of selection.recordings) {
    const key = item.primary_credits
      .map((credit) => `${credit.target_kind}:${credit.target.id}`)
      .sort()
      .join('|');
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }

  return (
    <Stack gap="md">
      <Stack gap="xs" component="nav" aria-label="Жанры исполнений">
        <Title order={2}>Жанры исполнений</Title>
        <div className={classes.facets}>
          <Anchor
            component={Link}
            href={selectionHref(pathname, {
              genreId: null,
              recordingId: selection.recordingId,
              textId: null,
            })}
            aria-current={selection.genreId === null ? 'page' : undefined}
            fw={selection.genreId === null ? 700 : 400}
          >
            Все
          </Anchor>
          {song.recording_genres.map((facet) => {
            const currentRecording = song.recordings.find(
              (item) => item.id === selection.recordingId,
            );
            const recordingId =
              currentRecording &&
              matchesRecordingGenre(currentRecording, facet.genre.id)
                ? currentRecording.id
                : (song.recordings.find((item) =>
                    matchesRecordingGenre(item, facet.genre.id),
                  )?.id ?? null);
            return (
              <Anchor
                component={Link}
                key={facet.genre.id}
                href={selectionHref(pathname, {
                  genreId: facet.genre.id,
                  recordingId,
                  textId: null,
                })}
                aria-current={
                  selection.genreId === facet.genre.id ? 'page' : undefined
                }
                fw={selection.genreId === facet.genre.id ? 700 : 400}
              >
                {facet.genre.name} ({facet.recording_count})
              </Anchor>
            );
          })}
        </div>
      </Stack>
      <Stack gap="sm" component="nav" aria-label="Хронология известных записей">
        <Title order={2}>Хронология известных записей</Title>
        <div className={classes.chronology}>
          {[...groups.entries()].map(([groupKey, items]) => {
            const names = items[0].primary_credits
              .map((credit) => credit.target.name)
              .join(', ');
            return (
              <Stack
                key={groupKey}
                gap="xs"
                className={classes.chronologyGroup}
              >
                <Text fw={600}>{names}</Text>
                {items.map((item) => (
                  <Anchor
                    component={Link}
                    key={item.id}
                    href={selectionHref(pathname, {
                      genreId: selection.genreId,
                      recordingId: item.id,
                      textId: null,
                    })}
                    aria-current={
                      selection.recordingId === item.id ? 'page' : undefined
                    }
                    fw={selection.recordingId === item.id ? 700 : 400}
                  >
                    {item.title}
                    {item.recorded_period.start
                      ? ` · ${formatTemporalBound(item.recorded_period.start)}`
                      : ''}
                    {item.origin_badges.map((badge) => (
                      <Badge key={badge} ml="xs" size="xs">
                        {formatOriginBadge(badge)}
                      </Badge>
                    ))}
                  </Anchor>
                ))}
              </Stack>
            );
          })}
        </div>
      </Stack>
    </Stack>
  );
}
