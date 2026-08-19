import { Container } from '@mantine/core';
import { notFound } from 'next/navigation';

import { PageError } from '@/shared/ui/PageError';
import { PerformerPageContent } from '@/features/performer-page/PerformerPageContent';
import { fetchPerformerOverview } from '@/shared/api/performer';

type PageProps = {
  params: Promise<{ performer_id: string }>;
};

export default async function PerformerPage({ params }: PageProps) {
  const { performer_id: performerId } = await params;
  const retryHref = `/performers/${encodeURIComponent(performerId)}`;
  const result = await fetchPerformerOverview(performerId);

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

  return <PerformerPageContent performer={result.data} />;
}
