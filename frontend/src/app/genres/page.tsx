import { Container } from '@mantine/core';

import { GenreCatalogContent } from '@/features/genre-catalog/GenreCatalogContent';
import { PageError } from '@/features/genre-page/PageError';
import { fetchPublishedGenres } from '@/shared/api/genre';

export default async function GenreCatalogPage() {
  const result = await fetchPublishedGenres();

  if (result.status !== 'ok') {
    return (
      <Container size="52rem" py="xl">
        <PageError
          message={
            result.status === 'error'
              ? result.message
              : 'Не удалось загрузить материал.'
          }
          retryHref="/genres"
        />
      </Container>
    );
  }

  return (
    <Container size="52rem" py="xl">
      <GenreCatalogContent items={result.data.items} />
    </Container>
  );
}
