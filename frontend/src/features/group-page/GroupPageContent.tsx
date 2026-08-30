'use client';

import {
  Anchor,
  Container,
  Grid,
  GridCol,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import Link from 'next/link';

import type { GroupOverview } from '@/shared/api/group';
import { PublicImage } from '@/shared/ui/PublicImage';

import { formatPeriod, hasPeriodBounds } from './labels';

export function GroupPageContent({
  group,
}: Readonly<{ group: GroupOverview }>) {
  const image = group.primary_image;
  const aliases = group.aliases;
  const groupPeriod = hasPeriodBounds(group.period)
    ? formatPeriod(group.period)
    : null;

  return (
    <Container size="52rem" py="xl" style={{ containerType: 'inline-size' }}>
      <Stack gap="xl" component="article">
        <Stack gap="md" component="section">
          <Grid type="container" gap="md">
            <GridCol span={{ base: 12, md: image ? 7 : 12 }}>
              <Stack gap="md">
                <Title order={1}>{group.name}</Title>
                {aliases.length > 0 ? (
                  <Text c="pastel.8" size="sm">
                    Также известна как: {aliases.join(', ')}
                  </Text>
                ) : null}
                {groupPeriod !== null ? (
                  <Text c="pastel.8" size="sm">
                    Период: {groupPeriod}
                  </Text>
                ) : null}
                {group.description !== null ? (
                  <Text>{group.description}</Text>
                ) : null}
              </Stack>
            </GridCol>
            {image !== null ? (
              <GridCol span={{ base: 12, md: 5 }}>
                <PublicImage image={image} />
              </GridCol>
            ) : null}
          </Grid>
        </Stack>

        {group.genres.length > 0 ? (
          <Stack gap="sm" component="section" aria-labelledby="genres-heading">
            <Title order={2} id="genres-heading">
              Жанры
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {group.genres.map((genre) => (
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

        {group.members.length > 0 ? (
          <Stack gap="sm" component="section" aria-labelledby="members-heading">
            <Title order={2} id="members-heading">
              Участники
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {group.members.map((member) => {
                const memberPeriod = hasPeriodBounds(member.period)
                  ? formatPeriod(member.period)
                  : null;
                const roles =
                  member.roles_or_instruments.length > 0
                    ? member.roles_or_instruments.join(', ')
                    : null;
                const details = [memberPeriod, roles]
                  .filter(Boolean)
                  .join('; ');

                return (
                  <li key={member.id}>
                    <Anchor
                      component={Link}
                      href={`/performers/${encodeURIComponent(member.id)}`}
                      c="pastel.7"
                      underline="always"
                    >
                      {member.name}
                    </Anchor>
                    {details.length > 0 ? (
                      <Text component="span" c="pastel.8" size="sm">
                        {' '}
                        ({details})
                      </Text>
                    ) : null}
                  </li>
                );
              })}
            </Stack>
          </Stack>
        ) : null}
      </Stack>
    </Container>
  );
}
