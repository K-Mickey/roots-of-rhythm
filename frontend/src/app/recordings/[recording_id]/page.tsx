import { Container } from '@mantine/core';
import { notFound } from 'next/navigation';

import { RecordingPageContent } from '@/features/recording-page/RecordingPageContent';
import { fetchRecordingOverview } from '@/shared/api/recording';
import { PageError } from '@/shared/ui/PageError';

export default async function RecordingPage({
  params,
}: Readonly<{
  params: Promise<{ recording_id: string }>;
}>) {
  const { recording_id: id } = await params;
  const result = await fetchRecordingOverview(id);
  if (result.status === 'not_found') notFound();
  if (result.status === 'error') {
    return (
      <Container size="72rem" py="xl">
        <PageError
          message={result.message}
          retryHref={`/recordings/${encodeURIComponent(id)}`}
        />
      </Container>
    );
  }
  return <RecordingPageContent recording={result.data} />;
}
