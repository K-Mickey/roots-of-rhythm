import { Anchor, Stack, Text, Title } from '@mantine/core';
import Link from 'next/link';

import {
  formatPeriod,
  hasPeriodBounds,
} from '@/features/song-page/labels';
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
            const performers = recording.primary_credits
              .map((credit) => credit.target.name)
              .join(', ');
            const genres = recording.genres.map((genre) => genre.name).join(', ');
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
                  {performers ? <Text size="sm">{performers}</Text> : null}
                  {period ? (
                    <Text size="sm" c="pastel.8">
                      Период записи: {period}
                    </Text>
                  ) : null}
                  {genres ? (
                    <Text size="sm" c="pastel.8">
                      {genres}
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
