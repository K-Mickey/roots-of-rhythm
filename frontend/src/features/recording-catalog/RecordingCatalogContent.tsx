'use client';

import { Anchor, Stack, Text, Title } from '@mantine/core';
import Link from 'next/link';

import { formatPeriod, hasPeriodBounds } from '@/features/song-page/labels';
import type { RecordingList } from '@/shared/api/recording';

export function RecordingCatalogContent({
  items,
}: {
  items: RecordingList['items'];
}) {
  return (
    <Stack gap="md">
      <Title order={1}>Записи</Title>
      {items.length > 0 ? (
        <Stack
          gap="md"
          component="ul"
          style={{ listStyle: 'none', padding: 0, margin: 0 }}
        >
          {items.map((recording) => {
            const period = hasPeriodBounds(recording.period)
              ? formatPeriod(recording.period)
              : null;
            return (
              <li key={recording.id}>
                <Stack gap={4}>
                  <Anchor
                    component={Link}
                    href={`/recordings/${encodeURIComponent(recording.id)}`}
                    c="pastel.7"
                    underline="always"
                    fw={600}
                  >
                    {recording.title}
                  </Anchor>
                  {recording.primary_credits.length ? (
                    <Text size="sm">
                      {recording.primary_credits.map((credit, index) => (
                        <span key={`${credit.target_kind}:${credit.target.id}`}>
                          {index > 0 ? ', ' : null}
                          <Anchor
                            component={Link}
                            href={`/${credit.target_kind === 'person' ? 'performers' : 'groups'}/${encodeURIComponent(credit.target.id)}`}
                          >
                            {credit.target.name}
                          </Anchor>
                        </span>
                      ))}
                    </Text>
                  ) : null}
                  {period ? (
                    <Text size="sm" c="pastel.8">
                      Период записи: {period}
                    </Text>
                  ) : null}
                  {recording.genres.length ? (
                    <Text size="sm" c="pastel.8">
                      {recording.genres.map((genre, index) => (
                        <span key={genre.id}>
                          {index > 0 ? ', ' : null}
                          <Anchor
                            component={Link}
                            href={`/genres/${encodeURIComponent(genre.id)}`}
                          >
                            {genre.name}
                          </Anchor>
                        </span>
                      ))}
                    </Text>
                  ) : null}
                </Stack>
              </li>
            );
          })}
        </Stack>
      ) : null}
    </Stack>
  );
}
