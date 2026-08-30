'use client';

import { Anchor, Stack, Title } from '@mantine/core';
import Link from 'next/link';

import type { PerformerList } from '@/shared/api/performer';

export function PerformerCatalogContent({
  items,
}: Readonly<{
  items: PerformerList['items'];
}>) {
  return (
    <Stack gap="md">
      <Title order={1}>Исполнители</Title>
      {items.length > 0 ? (
        <Stack
          gap="sm"
          component="ul"
          style={{ listStyle: 'none', padding: 0, margin: 0 }}
        >
          {items.map((performer) => (
            <li key={performer.id}>
              <Anchor
                component={Link}
                href={`/performers/${encodeURIComponent(performer.id)}`}
                c="pastel.7"
                underline="always"
              >
                {performer.name}
              </Anchor>
            </li>
          ))}
        </Stack>
      ) : null}
    </Stack>
  );
}
