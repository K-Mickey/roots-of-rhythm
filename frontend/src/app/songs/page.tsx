import { Container } from '@mantine/core';

import { SongCatalogContent } from '@/features/song-catalog/SongCatalogContent';
import { PageError } from '@/shared/ui/PageError';
import { fetchPublishedSongs } from '@/shared/api/song';

export default async function SongCatalogPage() {
  const result = await fetchPublishedSongs();

  if (result.status !== 'ok') {
    return (
      <Container size="52rem" py="xl">
        <PageError
          message={
            result.status === 'error'
              ? result.message
              : 'Не удалось загрузить материал.'
          }
          retryHref="/songs"
        />
      </Container>
    );
  }

  return (
    <Container size="52rem" py="xl">
      <SongCatalogContent items={result.data.items} />
    </Container>
  );
}
