import { Container } from '@mantine/core';

import { RecordingCatalogContent } from '@/features/recording-catalog/RecordingCatalogContent';
import { fetchPublishedRecordings } from '@/shared/api/recording';
import { PageError } from '@/shared/ui/PageError';

export default async function RecordingCatalogPage() {
  const result = await fetchPublishedRecordings();

  if (result.status !== 'ok') {
    return (
      <Container size="52rem" py="xl">
        <PageError
          message={
            result.status === 'error'
              ? result.message
              : 'Не удалось загрузить записи.'
          }
          retryHref="/recordings"
        />
      </Container>
    );
  }

  return (
    <Container size="52rem" py="xl">
      <RecordingCatalogContent items={result.data.items} />
    </Container>
  );
}
