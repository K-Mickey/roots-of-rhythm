import { Container } from '@mantine/core';
import { notFound } from 'next/navigation';

import { SongPageContent } from '@/features/song-page/SongPageContent';
import { PageError } from '@/shared/ui/PageError';
import { fetchSongOverview } from '@/shared/api/song';

type PageProps = {
  params: Promise<{ song_id: string }>;
};

export default async function SongPage({ params }: PageProps) {
  const { song_id: songId } = await params;
  const retryHref = `/songs/${encodeURIComponent(songId)}`;
  const result = await fetchSongOverview(songId);

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

  return <SongPageContent song={result.data} />;
}
