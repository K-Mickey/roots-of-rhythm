import { describe, expect, it } from 'vitest';

import type { SongOverview } from '@/shared/api/song';

import { resolveSongSelection, selectionHref } from './selection';

const song = {
  recording_genres: [
    { genre: { id: 'jazz', name: 'Jazz' }, recording_count: 1 },
  ],
  recordings: [
    { id: 'r1', genre_ids: ['jazz'], work_usage_kind: 'complete' },
    { id: 'r2', genre_ids: [], work_usage_kind: 'complete' },
    { id: 'medley', genre_ids: ['jazz'], work_usage_kind: 'medley_component' },
  ],
  lyrics_versions: [{ id: 'work-text' }],
} as SongOverview;

describe('song selection', () => {
  it('filters recordings and replaces foreign query values with safe defaults', () => {
    expect(
      resolveSongSelection(song, {
        genre: 'jazz',
        recording: 'r2',
        text: 'foreign',
      }),
    ).toEqual({
      genreId: 'jazz',
      recordingId: 'r1',
      textId: null,
      recordings: [song.recordings[0]],
    });
  });

  it('uses Work text only when the Work has no recordings', () => {
    const withoutRecordings = {
      ...song,
      recordings: [],
      recording_genres: [],
    };
    expect(resolveSongSelection(withoutRecordings, {}).textId).toBe(
      'work-text',
    );
  });

  it('keeps medley in the full chronology but excludes it from genre facets', () => {
    expect(resolveSongSelection(song, {}).recordings).toEqual(song.recordings);
    expect(
      resolveSongSelection(song, { genre: 'jazz', recording: 'medley' }),
    ).toMatchObject({
      genreId: 'jazz',
      recordingId: 'r1',
      recordings: [song.recordings[0]],
    });
  });

  it('builds canonical query URLs', () => {
    expect(
      selectionHref('/songs/song-1', {
        genreId: 'jazz',
        recordingId: 'r1',
        textId: null,
      }),
    ).toBe('/songs/song-1?genre=jazz&recording=r1');
  });
});
