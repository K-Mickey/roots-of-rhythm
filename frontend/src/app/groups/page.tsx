import { Container } from '@mantine/core';

import { GroupCatalogContent } from '@/features/group-catalog/GroupCatalogContent';
import { PageError } from '@/shared/ui/PageError';
import { fetchPublishedGroups } from '@/shared/api/group';

export default async function GroupCatalogPage() {
  const result = await fetchPublishedGroups();

  if (result.status !== 'ok') {
    return (
      <Container size="52rem" py="xl">
        <PageError
          message={
            result.status === 'error'
              ? result.message
              : 'Не удалось загрузить материал.'
          }
          retryHref="/groups"
        />
      </Container>
    );
  }

  return (
    <Container size="52rem" py="xl">
      <GroupCatalogContent items={result.data.items} />
    </Container>
  );
}
