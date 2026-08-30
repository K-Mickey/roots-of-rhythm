import { Grid, GridCol, Stack, Text, Title } from '@mantine/core';

import type { GenreOverview } from '@/shared/api/genre';

import { PublicImage } from '@/shared/ui/PublicImage';

export function GenreOverviewSection({
  overview,
}: Readonly<{
  overview: GenreOverview;
}>) {
  const hasHistoryBlock =
    overview.historical_context !== null ||
    overview.formation !== null ||
    overview.geography_or_origin !== null;
  const hasFeatures = overview.characteristic_features.length > 0;
  const image = overview.primary_image;

  return (
    <Stack
      gap="md"
      component="section"
      aria-labelledby="genre-overview-heading"
    >
      <Grid type="container" gap="md">
        <GridCol span={{ base: 12, md: image ? 7 : 12 }}>
          <Stack gap="md">
            <Title order={1} id="genre-overview-heading">
              {overview.name}
            </Title>
            {overview.period !== null ? (
              <Text c="pastel.8" size="sm">
                {overview.period.label}
              </Text>
            ) : null}
            <Text>{overview.definition}</Text>
          </Stack>
        </GridCol>
        {image !== null ? (
          <GridCol span={{ base: 12, md: 5 }}>
            <PublicImage image={image} />
          </GridCol>
        ) : null}
      </Grid>

      {hasHistoryBlock || hasFeatures ? (
        <Grid type="container" gap="md">
          {hasHistoryBlock ? (
            <GridCol span={{ base: 12, md: hasFeatures ? 6 : 12 }}>
              <GenreHistory overview={overview} />
            </GridCol>
          ) : null}
          {hasFeatures ? (
            <GridCol span={{ base: 12, md: hasHistoryBlock ? 6 : 12 }}>
              <GenreFeatures features={overview.characteristic_features} />
            </GridCol>
          ) : null}
        </Grid>
      ) : null}
    </Stack>
  );
}

function GenreHistory({ overview }: Readonly<{ overview: GenreOverview }>) {
  return (
    <Stack gap="sm">
      <Title order={2} id="genre-history-heading">
        Исторический контекст
      </Title>
      {overview.geography_or_origin !== null ? (
        <Text>{overview.geography_or_origin.summary}</Text>
      ) : null}
      {overview.historical_context !== null ? (
        <Text>{overview.historical_context}</Text>
      ) : null}
      {overview.formation !== null ? (
        <Stack gap="xs">
          <Title order={3}>Формирование</Title>
          <Text>{overview.formation}</Text>
        </Stack>
      ) : null}
    </Stack>
  );
}

function GenreFeatures({ features }: Readonly<{ features: string[] }>) {
  return (
    <Stack gap="sm">
      <Title order={2} id="genre-features-heading">
        Характерные черты
      </Title>
      <Stack
        gap="xs"
        component="ul"
        style={{ paddingInlineStart: '1.25rem', margin: 0 }}
      >
        {features.map((feature) => (
          <Text component="li" key={feature}>
            {feature}
          </Text>
        ))}
      </Stack>
    </Stack>
  );
}
