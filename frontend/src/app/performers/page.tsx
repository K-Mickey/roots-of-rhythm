import { Container } from '@mantine/core';

import { PerformerCatalogContent } from '@/features/performer-catalog/PerformerCatalogContent';
import { PageError } from '@/shared/ui/PageError';
import { fetchPublishedPerformers } from '@/shared/api/performer';

export default async function PerformerCatalogPage() {
  const result = await fetchPublishedPerformers();

  if (result.status !== 'ok') {
    return (
      <Container size="52rem" py="xl">
        <PageError
          message={
            result.status === 'error'
              ? result.message
              : 'Не удалось загрузить материал.'
          }
          retryHref="/performers"
        />
      </Container>
    );
  }

  return (
    <Container size="52rem" py="xl">
      <PerformerCatalogContent items={result.data.items} />
    </Container>
  );
}
