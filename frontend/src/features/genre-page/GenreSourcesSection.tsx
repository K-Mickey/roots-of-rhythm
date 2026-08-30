import { Anchor, Stack, Text, Title } from '@mantine/core';

import type { GenreSources } from '@/shared/api/genre';

export function GenreSourcesSection({
  sources,
}: Readonly<{
  sources: GenreSources['sources'];
}>) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <Stack gap="md" component="section" aria-labelledby="genre-sources-heading">
      <Title order={2} id="genre-sources-heading">
        Источники
      </Title>
      <Stack gap="sm" component="ol" style={{ paddingInlineStart: '1.25rem' }}>
        {sources.map((source, index) => {
          const attribution = [source.author, source.responsible_organization]
            .filter(Boolean)
            .join(' · ');
          const publication = [source.publication, source.publication_date]
            .filter(Boolean)
            .join(', ');

          return (
            <Stack
              gap={4}
              component="li"
              key={source.id}
              id={`source-${source.id}`}
            >
              <Text>
                <Text span fw={600}>
                  [{index + 1}] {source.title}
                </Text>
              </Text>
              {attribution !== '' ? (
                <Text size="sm" c="pastel.8">
                  {attribution}
                </Text>
              ) : null}
              {publication !== '' ? (
                <Text size="sm" c="pastel.8">
                  {publication}
                </Text>
              ) : null}
              {source.external_url !== null ? (
                <Anchor
                  href={source.external_url}
                  c="pastel.7"
                  target="_blank"
                  rel="noreferrer"
                >
                  {source.external_url}
                </Anchor>
              ) : null}
            </Stack>
          );
        })}
      </Stack>
    </Stack>
  );
}
