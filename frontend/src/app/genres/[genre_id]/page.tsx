import { Container } from '@mantine/core';
import { notFound } from 'next/navigation';

import { GenrePageContent } from '@/features/genre-page/GenrePageContent';
import { PageError } from '@/features/genre-page/PageError';
import { fetchGenrePage } from '@/shared/api/genre';

type PageProps = {
  params: Promise<{ genre_id: string }>;
};

export default async function GenrePage({ params }: PageProps) {
  const { genre_id: genreId } = await params;
  const retryHref = `/genres/${encodeURIComponent(genreId)}`;
  const projections = await fetchGenrePage(genreId);

  if (projections.overview.status === 'not_found') {
    notFound();
  }

  if (projections.overview.status === 'error') {
    return (
      <Container size="52rem" py="xl">
        <PageError
          message={projections.overview.message}
          retryHref={retryHref}
        />
      </Container>
    );
  }

  return (
    <GenrePageContent
      overview={projections.overview.data}
      relations={projections.relations}
      sources={projections.sources}
      retryHref={retryHref}
    />
  );
}
