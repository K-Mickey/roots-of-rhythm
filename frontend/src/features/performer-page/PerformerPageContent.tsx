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

import type { PerformerOverview } from '@/shared/api/performer';
import { PublicImage } from '@/shared/ui/PublicImage';

import { formatPersonDate, safeExternalHref } from './labels';

export function PerformerPageContent({
  performer,
}: {
  performer: PerformerOverview;
}) {
  const image = performer.primary_image;
  const aliases = performer.aliases;
  const birthDate = performer.birth_date;
  const deathDate = performer.death_date;
  const identities = performer.external_identities;

  return (
    <Container size="52rem" py="xl" style={{ containerType: 'inline-size' }}>
      <Stack gap="xl" component="article">
        <Stack gap="md" component="section">
          <Grid type="container" gap="md">
            <GridCol span={{ base: 12, md: image ? 7 : 12 }}>
              <Stack gap="md">
                <Title order={1}>{performer.name}</Title>
                {aliases.length > 0 ? (
                  <Text c="pastel.8" size="sm">
                    Также известен как: {aliases.join(', ')}
                  </Text>
                ) : null}
                {birthDate !== null ? (
                  <Text c="pastel.8" size="sm">
                    Родился: {formatPersonDate(birthDate)}
                  </Text>
                ) : null}
                {deathDate !== null ? (
                  <Text c="pastel.8" size="sm">
                    Умер: {formatPersonDate(deathDate)}
                  </Text>
                ) : null}
                {performer.biography !== null ? (
                  <Text>{performer.biography}</Text>
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

        {performer.genres.length > 0 ? (
          <Stack gap="sm" component="section" aria-labelledby="genres-heading">
            <Title order={2} id="genres-heading">
              Жанры
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {performer.genres.map((genre) => (
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

        {identities.length > 0 ? (
          <Stack
            gap="sm"
            component="section"
            aria-labelledby="identities-heading"
          >
            <Title order={2} id="identities-heading">
              Внешние идентификаторы
            </Title>
            <Stack
              gap="xs"
              component="ul"
              style={{ paddingInlineStart: '1.25rem', margin: 0 }}
            >
              {identities.map((identity) => {
                const href =
                  identity.url === null ? null : safeExternalHref(identity.url);
                const label = `${identity.provider}: ${identity.identifier}`;

                return (
                  <li key={`${identity.provider}:${identity.identifier}`}>
                    {href !== null ? (
                      <Anchor
                        href={href}
                        c="pastel.7"
                        underline="always"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {label}
                      </Anchor>
                    ) : (
                      <Text>{label}</Text>
                    )}
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
