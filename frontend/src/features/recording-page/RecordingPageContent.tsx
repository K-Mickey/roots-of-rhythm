'use client';

import { Anchor, Badge, Container, Stack, Text, Title } from '@mantine/core';
import Link from 'next/link';

import type { RecordingOverview } from '@/shared/api/recording';

import { formatOriginBadge, formatRecordingWorkUsageKind } from './labels';
import { RecordingLyricsSection } from './RecordingLyricsSection';
import classes from './RecordingPageContent.module.css';

export function RecordingPageContent({
  recording,
}: Readonly<{
  recording: RecordingOverview;
}>) {
  return (
    <Container size="72rem" py="xl" style={{ containerType: 'inline-size' }}>
      <div className={classes.detailGrid}>
        <RecordingDetails
          recording={recording}
          showWorks={false}
          showCredits={false}
          normalizeLyricsQuery
        />
        <Stack component="aside" gap="xl" className={classes.sidebar}>
          <RecordingWorks recording={recording} order={2} />
          <RecordingCredits recording={recording} order={2} />
        </Stack>
      </div>
    </Container>
  );
}

export function RecordingDetails({
  recording,
  headingOrder = 1,
  showWorks = true,
  showCredits = true,
  showLyrics = true,
  excludeWorkId,
  lyricsSelectedId,
  normalizeLyricsQuery = false,
  originBadges = recording.origin_badges,
}: Readonly<{
  recording: RecordingOverview;
  headingOrder?: 1 | 2;
  showWorks?: boolean;
  showCredits?: boolean;
  showLyrics?: boolean;
  excludeWorkId?: string;
  lyricsSelectedId?: string | null;
  normalizeLyricsQuery?: boolean;
  originBadges?: RecordingOverview['origin_badges'];
}>) {
  const period = [recording.period.start?.year, recording.period.end?.year]
    .filter((year) => year !== undefined)
    .join(' — ');
  const sectionOrder = headingOrder === 1 ? 2 : 3;
  return (
    <Stack
      gap="xl"
      component={headingOrder === 1 ? 'article' : 'section'}
      className={classes.main}
    >
      <Stack gap="sm">
        <Title order={headingOrder}>{recording.title}</Title>
        {originBadges.length ? (
          <Stack component="section" gap="xs" aria-label="Исторические отметки">
            {originBadges.map((badge) => (
              <Badge key={badge}>{formatOriginBadge(badge)}</Badge>
            ))}
          </Stack>
        ) : null}
        {recording.description ? <Text>{recording.description}</Text> : null}
        {period ? <Text size="sm">Период записи: {period}</Text> : null}
        {recording.isrc ? <Text size="sm">ISRC: {recording.isrc}</Text> : null}
      </Stack>
      {showWorks ? (
        <RecordingWorks
          recording={recording}
          order={sectionOrder}
          excludeWorkId={excludeWorkId}
        />
      ) : null}
      {showCredits ? (
        <RecordingCredits recording={recording} order={sectionOrder} />
      ) : null}
      <RecordingGenres recording={recording} order={sectionOrder} />
      {showLyrics && recording.lyrics.length ? (
        <RecordingLyricsSection
          versions={recording.lyrics}
          selectedId={lyricsSelectedId}
          headingOrder={sectionOrder}
          normalizeQuery={normalizeLyricsQuery}
        />
      ) : null}
      <RecordingListeningGuide recording={recording} order={sectionOrder} />
    </Stack>
  );
}

function RecordingWorks({
  recording,
  order,
  excludeWorkId,
}: Readonly<{
  recording: RecordingOverview;
  order: 2 | 3;
  excludeWorkId?: string;
}>) {
  const works = recording.works.filter(
    (item) => item.work.id !== excludeWorkId,
  );
  return works.length ? (
    <Section title="Произведения" order={order}>
      {works.map((item) => {
        const usageLabel = formatRecordingWorkUsageKind(item.usage_kind);
        return (
          <li key={`${item.work.id}:${item.usage_kind}`}>
            {usageLabel ? `${usageLabel}: ` : null}
            <Anchor
              component={Link}
              href={`/songs/${encodeURIComponent(item.work.id)}`}
            >
              {item.work.name}
            </Anchor>
          </li>
        );
      })}
    </Section>
  ) : null;
}

function RecordingCredits({
  recording,
  order,
}: Readonly<{
  recording: RecordingOverview;
  order: 2 | 3;
}>) {
  return recording.credits.length ? (
    <Section title="Исполнители" order={order}>
      {recording.credits.map((item) => (
        <li key={`${item.target_kind}:${item.target.id}:${item.billing_role}`}>
          <Anchor
            component={Link}
            href={`/${item.target_kind === 'person' ? 'performers' : 'groups'}/${encodeURIComponent(item.target.id)}`}
          >
            {item.target.name}
          </Anchor>
          {item.credited_as ? ` (как ${item.credited_as})` : ''}
          {item.instrument ? ` — ${item.instrument}` : ''}
        </li>
      ))}
    </Section>
  ) : null;
}

function Section({
  title,
  children,
  order = 2,
}: Readonly<{
  title: string;
  children: React.ReactNode;
  order?: 2 | 3;
}>) {
  return (
    <Stack component="section" gap="sm">
      <Title order={order}>{title}</Title>
      <Stack
        component="ul"
        gap="xs"
        style={{ paddingInlineStart: '1.25rem', margin: 0 }}
      >
        {children}
      </Stack>
    </Stack>
  );
}

function RecordingGenres({
  recording,
  order,
}: Readonly<{ recording: RecordingOverview; order: 2 | 3 }>) {
  if (!recording.genres.length) return null;
  return (
    <Section title="Жанры" order={order}>
      {recording.genres.map((item) => (
        <li key={item.id}>
          <Anchor
            component={Link}
            href={`/genres/${encodeURIComponent(item.id)}`}
          >
            {item.name}
          </Anchor>
        </li>
      ))}
    </Section>
  );
}

function RecordingListeningGuide({
  recording,
  order,
}: Readonly<{ recording: RecordingOverview; order: 2 | 3 }>) {
  const guide = recording.listening_guide;
  if (!guide) return null;
  return (
    <Section title="На что обратить внимание" order={order}>
      {guide.observations.map((item) => (
        <li key={item.position}>
          <Text fw={600}>{item.feature}</Text>
          <Text>{item.explanation}</Text>
          {item.context ? <Text size="sm">{item.context}</Text> : null}
          {item.start_seconds !== null && item.end_seconds !== null ? (
            <Text size="sm">
              {item.start_seconds}–{item.end_seconds} сек.
            </Text>
          ) : null}
        </li>
      ))}
    </Section>
  );
}
