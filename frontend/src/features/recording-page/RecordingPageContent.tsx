import { Anchor, Badge, Container, Stack, Text, Title } from '@mantine/core';
import Link from 'next/link';

import type { RecordingOverview } from '@/shared/api/recording';

import { formatRecordingWorkUsageKind } from './labels';

export function RecordingPageContent({
  recording,
}: {
  recording: RecordingOverview;
}) {
  const period = [recording.period.start?.year, recording.period.end?.year]
    .filter((year) => year !== undefined)
    .join(' — ');
  return (
    <Container size="52rem" py="xl">
      <Stack gap="xl" component="article">
        <Stack gap="sm">
          <Title order={1}>{recording.title}</Title>
          {recording.description ? <Text>{recording.description}</Text> : null}
          {period ? <Text size="sm">Период записи: {period}</Text> : null}
          {recording.isrc ? (
            <Text size="sm">ISRC: {recording.isrc}</Text>
          ) : null}
        </Stack>
        {recording.works.length ? (
          <Section title="Произведения">
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
          <Section title="Исполнители">
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
          <Section title="Жанры">
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
        {recording.lyrics.length ? (
          <Stack component="section">
            <Title order={2}>Текст</Title>
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
          <Section title="На что обратить внимание">
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
    </Container>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Stack component="section" gap="sm">
      <Title order={2}>{title}</Title>
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
