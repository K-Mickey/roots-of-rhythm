'use client';

import { Anchor, Stack, Title } from '@mantine/core';
import Link from 'next/link';

import type { SongList } from '@/shared/api/song';

export function SongCatalogContent({ items }: { items: SongList['items'] }) {
  return (
    <Stack gap="md">
      <Title order={1}>Песни</Title>
      {items.length > 0 ? (
        <Stack
          gap="sm"
          component="ul"
          style={{ listStyle: 'none', padding: 0, margin: 0 }}
        >
          {items.map((song) => (
            <li key={song.id}>
              <Anchor
                component={Link}
                href={`/songs/${encodeURIComponent(song.id)}`}
                c="pastel.7"
                underline="always"
              >
                {song.name}
              </Anchor>
            </li>
          ))}
        </Stack>
      ) : null}
    </Stack>
  );
}
