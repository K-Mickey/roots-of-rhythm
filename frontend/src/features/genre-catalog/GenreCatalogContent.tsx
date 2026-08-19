'use client';

import { Anchor, Stack, Title } from '@mantine/core';
import Link from 'next/link';

import type { GenreList } from '@/shared/api/genre';

export function GenreCatalogContent({ items }: { items: GenreList['items'] }) {
  return (
    <Stack gap="md">
      <Title order={1}>Жанры</Title>
      {items.length > 0 ? (
        <Stack
          gap="sm"
          component="ul"
          style={{ listStyle: 'none', padding: 0, margin: 0 }}
        >
          {items.map((genre) => (
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
      ) : null}
    </Stack>
  );
}
