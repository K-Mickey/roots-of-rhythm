import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { SongOverview } from '@/shared/api/song';
import { createAppTheme } from '@/shared/theme/theme';

import { SongPageContent } from './SongPageContent';

const replaceMock = vi.fn();
const searchParams = new URLSearchParams();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: replaceMock,
  }),
  usePathname: () => '/songs/song-1',
  useSearchParams: () => searchParams,
}));

afterEach(() => {
  cleanup();
  replaceMock.mockClear();
  for (const key of [...searchParams.keys()]) {
    searchParams.delete(key);
  }
});

beforeEach(() => {
  replaceMock.mockClear();
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
    expect(screen.getByRole('tab', { name: /en · Original/ })).toBeInTheDocument();
    expect(
      screen.getByRole('tab', { name: /ru · машинный перевод/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Текст недоступен по правам.'),
    ).toBeInTheDocument();
  });

  it('falls back to the first lyrics version for an invalid text query', () => {
    searchParams.set('text', 'invalid');
    renderWithProviders(<SongPageContent song={populatedOverview} />);

    expect(screen.getByText('First line')).toBeInTheDocument();
    expect(replaceMock).toHaveBeenCalledWith(
      '/songs/song-1?text=lyrics-1',
      { scroll: false },
    );

    fireEvent.click(screen.getByRole('tab', { name: /ru · машинный перевод/ }));
    expect(replaceMock).toHaveBeenLastCalledWith(
      '/songs/song-1?text=lyrics-2',
      { scroll: false },
    );
  });
});
