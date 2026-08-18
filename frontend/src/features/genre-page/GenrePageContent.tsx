import { Container, Stack } from '@mantine/core';

import type {
  GenreOverview,
  ProjectionResult,
  GenreRelations,
  GenreSources,
} from '@/shared/api/genre';

import { GenreOverviewSection } from './GenreOverviewSection';
import { GenreRelationsSection } from './GenreRelationsSection';
import { GenreSourcesSection } from './GenreSourcesSection';
import { SectionError } from './SectionError';

export function GenrePageContent({
  overview,
  relations,
  sources,
  retryHref,
}: {
  overview: GenreOverview;
  relations: ProjectionResult<GenreRelations>;
  sources: ProjectionResult<GenreSources>;
  retryHref: string;
}) {
  const loadedSources = sources.status === 'ok' ? sources.data.sources : [];

  return (
    <Container size="52rem" py="xl" style={{ containerType: 'inline-size' }}>
      <Stack gap="xl" component="article">
        <GenreOverviewSection overview={overview} />

        {relations.status === 'ok' ? (
          <GenreRelationsSection
            relations={relations.data.relations}
            sources={loadedSources}
          />
        ) : relations.status === 'not_found' || relations.status === 'error' ? (
          <SectionError
            title="Связи"
            message={
              relations.status === 'error'
                ? relations.message
                : 'Не удалось загрузить связи.'
            }
            retryHref={retryHref}
          />
        ) : null}

        {sources.status === 'ok' ? (
          <GenreSourcesSection sources={sources.data.sources} />
        ) : sources.status === 'not_found' || sources.status === 'error' ? (
          <SectionError
            title="Источники"
            message={
              sources.status === 'error'
                ? sources.message
                : 'Не удалось загрузить источники.'
            }
            retryHref={retryHref}
          />
        ) : null}
      </Stack>
    </Container>
  );
}
