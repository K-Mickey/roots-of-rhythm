import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { SongOverview } from '@/shared/api/song';
import type { RecordingOverview } from '@/shared/api/recording';
import { createAppTheme } from '@/shared/theme/theme';

import { SongPageContent } from './SongPageContent';

const replaceMock = vi.fn();
const pushMock = vi.fn();
const searchParams = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: replaceMock,
    push: pushMock,
  }),
  usePathname: () => '/songs/song-1',
  useSearchParams: () => searchParams,
}));

afterEach(() => {
  cleanup();
  replaceMock.mockClear();
  pushMock.mockClear();
  for (const key of [...searchParams.keys()]) {
    searchParams.delete(key);
  }
});

beforeEach(() => {
  replaceMock.mockClear();
  pushMock.mockClear();
});

function renderWithProviders(ui: ReactElement) {
  return render(
    <MantineProvider theme={createAppTheme('Source Sans 3, sans-serif')}>
      {ui}
    </MantineProvider>,
  );
}

const emptyOverview: SongOverview = {
  id: 'song-1',
  name: 'Sixteen Tons',
  aliases: [],
  description: null,
  period: { start: null, end: null },
  external_identities: [],
  credits: [],
  classifications: [],
  related_works: [],
  lyrics_versions: [],
  recording_genres: [],
  recordings: [],
};

const populatedOverview: SongOverview = {
  id: 'song-2',
  name: "One O'Clock Jump",
  aliases: ['Jump'],
  description: 'A swing standard.',
  period: {
    start: { year: 1937, precision: 'exact_year' },
    end: null,
  },
  external_identities: [
    {
      provider: 'MusicBrainz',
      identifier: 'mb-1',
      url: 'https://musicbrainz.org/work/1',
    },
  ],
  credits: [
    {
      person: { id: 'performer-1', name: 'Count Basie' },
      role: 'composer',
      credited_as: null,
    },
  ],
  classifications: [{ id: 'swing', name: 'Swing' }],
  related_works: [
    {
      relation_type: 'arrangement_of',
      work: { id: 'song-3', name: 'Ornithology' },
    },
  ],
  lyrics_versions: [
    {
      id: 'lyrics-1',
      language_tag: 'en',
      label: 'Original',
      usage_kind: 'performable',
      creation_method: 'original',
      body: 'First line',
      body_unavailable_reason: null,
      credits: [],
      relations: [],
    },
    {
      id: 'lyrics-2',
      language_tag: 'ru',
      label: null,
      usage_kind: 'reading_translation',
      creation_method: 'machine_translation',
      body: null,
      body_unavailable_reason: 'Текст недоступен по правам.',
      credits: [],
      relations: [],
    },
  ],
  recording_genres: [],
  recordings: [],
};

const selectedRecording: RecordingOverview = {
  id: 'recording-1',
  title: '1937 Studio Take',
  period: { start: { year: 1937, precision: 'exact_year' }, end: null },
  description: null,
  isrc: null,
  first_release_date: null,
  works: [
    {
      work: { id: 'song-2', name: "One O'Clock Jump" },
      usage_kind: 'complete',
      position: null,
    },
  ],
  credits: [
    {
      target_kind: 'group',
      target: { id: 'group-1', name: 'Count Basie Orchestra' },
      billing_role: 'primary',
      contribution_kind: null,
      instrument: null,
      credited_as: null,
    },
  ],
  genres: [{ id: 'swing', name: 'Swing' }],
  lyrics: [
    {
      id: 'recording-text',
      language_tag: 'en',
      label: null,
      creation_method: 'original',
      body: 'Recorded words',
      body_unavailable_reason: null,
      position: 1,
      confirmed_for_recording: true,
    },
  ],
  listening_guide: null,
  origin_badges: ['first_recording_of'],
};

const overviewWithRecordings: SongOverview = {
  ...populatedOverview,
  recording_genres: [
    { genre: { id: 'swing', name: 'Swing' }, recording_count: 2 },
  ],
  recordings: [
    {
      id: 'recording-1',
      title: '1937 Studio Take',
      recorded_period: selectedRecording.period,
      first_release_date: null,
      primary_credits: [
        {
          target_kind: 'group',
          target: { id: 'group-1', name: 'Count Basie Orchestra' },
        },
      ],
      genre_ids: ['swing'],
      work_usage_kind: 'complete',
      origin_badges: ['first_recording_of'],
    },
    {
      id: 'recording-2',
      title: 'Live Take',
      recorded_period: { start: null, end: null },
      first_release_date: null,
      primary_credits: [
        {
          target_kind: 'group',
          target: { id: 'group-1', name: 'Count Basie Orchestra' },
        },
      ],
      genre_ids: ['swing'],
      work_usage_kind: 'complete',
      origin_badges: [],
    },
  ],
};

describe('SongPageContent', () => {
  it('renders optional aliases, description, period, credits, classifications, and related works', () => {
    renderWithProviders(<SongPageContent song={populatedOverview} />);

    expect(
      screen.getByRole('heading', { level: 1, name: "One O'Clock Jump" }),
    ).toBeInTheDocument();
    expect(screen.getByText('Также известна как: Jump')).toBeInTheDocument();
    expect(screen.getByText('Период: 1937')).toBeInTheDocument();
    expect(screen.getByText('A swing standard.')).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Внешние идентификаторы' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'MusicBrainz: mb-1' }),
    ).toHaveAttribute('href', 'https://musicbrainz.org/work/1');
    expect(screen.getByRole('heading', { name: 'Авторы' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Count Basie' })).toHaveAttribute(
      'href',
      '/performers/performer-1',
    );
    expect(screen.getByText(/композитор/)).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Классификация произведения' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Swing' })).toHaveAttribute(
      'href',
      '/genres/swing',
    );
    expect(
      screen.getByRole('heading', { name: 'Связанные произведения' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ornithology' })).toHaveAttribute(
      'href',
      '/songs/song-3',
    );
    expect(screen.getByText(/аранжировка/)).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Записи' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Послушать' }),
    ).not.toBeInTheDocument();
  });

  it('omits empty optional sections from the DOM', () => {
    renderWithProviders(<SongPageContent song={emptyOverview} />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Sixteen Tons' }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Также известна как/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Период:/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Авторы' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Классификация произведения' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Связанные произведения' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Текст' }),
    ).not.toBeInTheDocument();
  });

  it('renders lyrics versions, unavailable body message, and machine translation label', () => {
    searchParams.set('text', 'lyrics-2');
    renderWithProviders(<SongPageContent song={populatedOverview} />);

    expect(screen.getByRole('heading', { name: 'Текст' })).toBeInTheDocument();
    expect(
      screen.getByRole('tab', { name: /en · Original/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('tab', { name: /ru · машинный перевод/ }),
    ).toBeInTheDocument();
    expect(screen.getByText('Текст недоступен по правам.')).toBeInTheDocument();
  });

  it('falls back to the first lyrics version for an invalid text query', () => {
    searchParams.set('text', 'invalid');
    renderWithProviders(<SongPageContent song={populatedOverview} />);

    expect(screen.getByText('First line')).toBeInTheDocument();
    expect(replaceMock).toHaveBeenCalledWith('/songs/song-1?text=lyrics-1', {
      scroll: false,
    });

    fireEvent.click(screen.getByRole('tab', { name: /ru · машинный перевод/ }));
    expect(pushMock).toHaveBeenLastCalledWith('/songs/song-1?text=lyrics-2', {
      scroll: false,
    });
  });

  it('renders selected Recording, facets, grouped chronology, and exact origin label', () => {
    searchParams.set('genre', 'swing');
    searchParams.set('recording', 'recording-1');
    searchParams.set('text', 'recording-text');
    renderWithProviders(
      <SongPageContent
        song={overviewWithRecordings}
        recording={selectedRecording}
      />,
    );

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(
      screen.getByRole('heading', { level: 2, name: '1937 Studio Take' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('navigation', { name: 'Жанры исполнений' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('navigation', { name: 'Хронология известных записей' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Live Take' })).toHaveAttribute(
      'href',
      '/songs/song-1?genre=swing&recording=recording-2',
    );
    expect(
      screen.getAllByText('Первая известная запись').length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText(/^Оригинал$/)).not.toBeInTheDocument();
    expect(screen.getByText('Recorded words')).toBeInTheDocument();
  });

  it('scopes origin badges to the Work and renders the selected Recording guide', () => {
    searchParams.set('recording', 'recording-1');
    renderWithProviders(
      <SongPageContent
        song={overviewWithRecordings}
        recording={{
          ...selectedRecording,
          origin_badges: ['first_released_recording_of'],
          listening_guide: {
            observations: [
              {
                feature: 'Слушайте ритм-секцию',
                explanation: 'Она удерживает пульс.',
                context: null,
                position: 1,
                start_seconds: null,
                end_seconds: null,
              },
            ],
          },
        }}
      />,
    );

    expect(screen.getAllByText('Первая известная запись')).not.toHaveLength(0);
    expect(
      screen.queryByText('Первая выпущенная запись'),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'На что обратить внимание' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Слушайте ритм-секцию')).toBeInTheDocument();
  });

  it('marks fallback lyrics and does not render a stale Recording detail', () => {
    searchParams.set('recording', 'recording-1');
    const fallbackRecording = {
      ...selectedRecording,
      lyrics: [
        {
          ...selectedRecording.lyrics[0],
          confirmed_for_recording: false,
        },
      ],
    };
    renderWithProviders(
      <SongPageContent
        song={overviewWithRecordings}
        recording={fallbackRecording}
      />,
    );
    expect(
      screen.getByText('Соответствие текста этой записи не подтверждено'),
    ).toBeInTheDocument();

    cleanup();
    renderWithProviders(
      <SongPageContent
        song={overviewWithRecordings}
        recording={{ ...selectedRecording, id: 'recording-2' }}
      />,
    );
    expect(
      screen.queryByRole('heading', { level: 2, name: '1937 Studio Take' }),
    ).not.toBeInTheDocument();
  });
});
