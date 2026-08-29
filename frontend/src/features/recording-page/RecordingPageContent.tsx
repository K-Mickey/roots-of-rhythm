import { Anchor, Badge, Container, Stack, Text, Title } from '@mantine/core';
import Link from 'next/link';

import type { RecordingOverview } from '@/shared/api/recording';

import { formatOriginBadge, formatRecordingWorkUsageKind } from './labels';

export function RecordingPageContent({
  recording,
}: {
  recording: RecordingOverview;
}) {
  return (
    <Container size="52rem" py="xl">
      <RecordingDetails recording={recording} />
    </Container>
  );
}

export function RecordingDetails({
  recording,
  headingOrder = 1,
  showWorks = true,
  showLyrics = true,
  originBadges = recording.origin_badges,
}: {
  recording: RecordingOverview;
  headingOrder?: 1 | 2;
  showWorks?: boolean;
  showLyrics?: boolean;
  originBadges?: RecordingOverview['origin_badges'];
}) {
  const period = [recording.period.start?.year, recording.period.end?.year]
    .filter((year) => year !== undefined)
    .join(' — ');
  return (
    <Stack gap="xl" component={headingOrder === 1 ? 'article' : 'section'}>
      <Stack gap="sm">
        <Title order={headingOrder}>{recording.title}</Title>
        {recording.description ? <Text>{recording.description}</Text> : null}
        {period ? <Text size="sm">Период записи: {period}</Text> : null}
        {recording.isrc ? <Text size="sm">ISRC: {recording.isrc}</Text> : null}
      </Stack>
      {showWorks && recording.works.length ? (
        <Section title="Произведения" order={headingOrder === 1 ? 2 : 3}>
          {recording.works.map((item) => {
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
      ) : null}
      {recording.credits.length ? (
        <Section title="Исполнители" order={headingOrder === 1 ? 2 : 3}>
          {recording.credits.map((item) => (
            <li
              key={`${item.target_kind}:${item.target.id}:${item.billing_role}`}
            >
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
      ) : null}
      {recording.genres.length ? (
        <Section title="Жанры" order={headingOrder === 1 ? 2 : 3}>
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
      ) : null}
      {originBadges.length ? (
        <Stack component="section" gap="xs" aria-label="Исторические отметки">
          {originBadges.map((badge) => (
            <Badge key={badge}>{formatOriginBadge(badge)}</Badge>
          ))}
        </Stack>
      ) : null}
      {showLyrics && recording.lyrics.length ? (
        <Stack component="section">
          <Title order={headingOrder === 1 ? 2 : 3}>Текст</Title>
          {recording.lyrics.map((item) => (
            <Stack key={item.id} gap="xs">
              <Text fw={600}>
                {item.label ?? item.language_tag}
                {item.creation_method === 'machine_translation' ? (
                  <Badge ml="xs">Машинный перевод</Badge>
                ) : null}
              </Text>
              {!item.confirmed_for_recording ? (
                <Text size="sm">
                  Соответствие текста этой записи не подтверждено
                </Text>
              ) : null}
              <Text style={{ whiteSpace: 'pre-wrap' }}>
                {item.body ??
                  item.body_unavailable_reason ??
                  'Текст недоступен для просмотра.'}
              </Text>
            </Stack>
          ))}
        </Stack>
      ) : null}
      {recording.listening_guide ? (
        <Section
          title="На что обратить внимание"
          order={headingOrder === 1 ? 2 : 3}
        >
          {recording.listening_guide.observations.map((item) => (
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
      ) : null}
    </Stack>
  );
}

function Section({
  title,
  children,
  order = 2,
}: {
  title: string;
  children: React.ReactNode;
  order?: 2 | 3;
}) {
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
