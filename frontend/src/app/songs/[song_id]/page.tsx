import { Container } from '@mantine/core';
import { notFound } from 'next/navigation';

import { SongPageContent } from '@/features/song-page/SongPageContent';
import { resolveSongSelection } from '@/features/song-page/selection';
import { fetchRecordingOverview } from '@/shared/api/recording';
import { PageError } from '@/shared/ui/PageError';
import { fetchSongOverview } from '@/shared/api/song';

type PageProps = Readonly<{
  params: Promise<{ song_id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}>;

export default async function SongPage({ params, searchParams }: PageProps) {
  const { song_id: songId } = await params;
  const queryParams = await searchParams;
  const query = {
    genre: first(queryParams.genre),
    recording: first(queryParams.recording),
    text: first(queryParams.text),
  };
  const retryHref = `/songs/${encodeURIComponent(songId)}`;
  const result = await fetchSongOverview(songId);

  if (result.status === 'not_found') {
    notFound();
  }

  if (result.status === 'error') {
    return (
      <Container size="72rem" py="xl">
        <PageError message={result.message} retryHref={retryHref} />
      </Container>
    );
  }

  const initialSelection = resolveSongSelection(result.data, query);
  if (initialSelection.recordingId === null) {
    return <SongPageContent song={result.data} recording={null} />;
  }

  const recordingResult = await fetchRecordingOverview(
    initialSelection.recordingId,
  );
  if (recordingResult.status !== 'ok') {
    return (
      <Container size="72rem" py="xl">
        <PageError
          message={
            recordingResult.status === 'error'
              ? recordingResult.message
              : 'Не удалось загрузить выбранную запись.'
          }
          retryHref={retryHref}
        />
      </Container>
    );
  }

  return (
    <SongPageContent song={result.data} recording={recordingResult.data} />
  );
}

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}
