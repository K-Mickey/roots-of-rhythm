import type { RecordingOverview } from '@/shared/api/recording';
import type { SongOverview } from '@/shared/api/song';

export type SongSelection = {
  genreId: string | null;
  recordingId: string | null;
  textId: string | null;
  recordings: SongOverview['recordings'];
};

export function matchesRecordingGenre(
  recording: SongOverview['recordings'][number],
  genreId: string,
): boolean {
  return (
    recording.work_usage_kind !== 'medley_component' &&
    recording.genre_ids.includes(genreId)
  );
}

export function resolveSongSelection(
  song: SongOverview,
  query: { genre?: string; recording?: string; text?: string },
  recording: RecordingOverview | null = null,
): SongSelection {
  const genreId = song.recording_genres.some(
    (facet) => facet.genre.id === query.genre,
  )
    ? (query.genre ?? null)
    : null;
  const recordings = genreId
    ? song.recordings.filter((item) => matchesRecordingGenre(item, genreId))
    : song.recordings;
  const selected =
    recordings.find((item) => item.id === query.recording) ??
    recordings[0] ??
    null;
  const versions =
    recording !== null && selected !== null && recording.id === selected.id
      ? recording.lyrics
      : selected === null
        ? song.lyrics_versions
        : [];
  const textId =
    versions.find((version) => version.id === query.text)?.id ??
    versions[0]?.id ??
    null;
  return {
    genreId,
    recordingId: selected?.id ?? null,
    textId,
    recordings,
  };
}

export function selectionHref(
  pathname: string,
  selection: {
    genreId: string | null;
    recordingId: string | null;
    textId: string | null;
  },
): string {
  const params = new URLSearchParams();
  if (selection.genreId) params.set('genre', selection.genreId);
  if (selection.recordingId) params.set('recording', selection.recordingId);
  if (selection.textId) params.set('text', selection.textId);
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}
