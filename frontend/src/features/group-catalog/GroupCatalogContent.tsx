'use client';

import { Anchor, Stack, Title } from '@mantine/core';
import Link from 'next/link';

import type { GroupList } from '@/shared/api/group';

export function GroupCatalogContent({
  items,
}: Readonly<{ items: GroupList['items'] }>) {
  return (
    <Stack gap="md">
      <Title order={1}>Группы</Title>
      {items.length > 0 ? (
        <Stack
          gap="sm"
          component="ul"
          style={{ listStyle: 'none', padding: 0, margin: 0 }}
        >
          {items.map((group) => (
            <li key={group.id}>
              <Anchor
                component={Link}
                href={`/groups/${encodeURIComponent(group.id)}`}
                c="pastel.7"
                underline="always"
              >
                {group.name}
              </Anchor>
            </li>
          ))}
        </Stack>
      ) : null}
    </Stack>
  );
}
