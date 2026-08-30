import { Container, Stack } from '@mantine/core';
import type { ReactNode } from 'react';

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
}: Readonly<{
  overview: GenreOverview;
  relations: ProjectionResult<GenreRelations>;
  sources: ProjectionResult<GenreSources>;
  retryHref: string;
}>) {
  const loadedSources = sources.status === 'ok' ? sources.data.sources : [];
  let relationsContent: ReactNode = null;
  if (relations.status === 'ok') {
    relationsContent = (
      <GenreRelationsSection
        relations={relations.data.relations}
        sources={loadedSources}
      />
    );
  } else if (relations.status === 'not_found' || relations.status === 'error') {
    relationsContent = (
      <SectionError
        title="Связи"
        message={
          relations.status === 'error'
            ? relations.message
            : 'Не удалось загрузить связи.'
        }
        retryHref={retryHref}
      />
    );
  }

  let sourcesContent: ReactNode = null;
  if (sources.status === 'ok') {
    sourcesContent = <GenreSourcesSection sources={sources.data.sources} />;
  } else if (sources.status === 'not_found' || sources.status === 'error') {
    sourcesContent = (
      <SectionError
        title="Источники"
        message={
          sources.status === 'error'
            ? sources.message
            : 'Не удалось загрузить источники.'
        }
        retryHref={retryHref}
      />
    );
  }

  return (
    <Container size="52rem" py="xl" style={{ containerType: 'inline-size' }}>
      <Stack gap="xl" component="article">
        <GenreOverviewSection overview={overview} />

        {relationsContent}
        {sourcesContent}
      </Stack>
    </Container>
  );
}
