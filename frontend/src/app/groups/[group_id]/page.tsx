import { Container } from '@mantine/core';
import { notFound } from 'next/navigation';

import { PageError } from '@/shared/ui/PageError';
import { GroupPageContent } from '@/features/group-page/GroupPageContent';
import { fetchGroupOverview } from '@/shared/api/group';

type PageProps = {
  params: Promise<{ group_id: string }>;
};

export default async function GroupPage({ params }: PageProps) {
  const { group_id: groupId } = await params;
  const retryHref = `/groups/${encodeURIComponent(groupId)}`;
  const result = await fetchGroupOverview(groupId);

  if (result.status === 'not_found') {
    notFound();
  }

  if (result.status === 'error') {
    return (
      <Container size="52rem" py="xl">
        <PageError message={result.message} retryHref={retryHref} />
      </Container>
    );
  }

  return <GroupPageContent group={result.data} />;
}
