import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import type { PerformerOverview } from '@/shared/api/performer';
import { createAppTheme } from '@/shared/theme/theme';

import { PerformerPageContent } from './PerformerPageContent';

afterEach(() => {
  cleanup();
});

function renderWithProviders(ui: ReactElement) {
  return render(
    <MantineProvider theme={createAppTheme('Source Sans 3, sans-serif')}>
      {ui}
    </MantineProvider>,
  );
}

const emptyOverview: PerformerOverview = {
  id: 'performer-1',
  name: 'Count Basie',
  biography: null,
  primary_image: null,
  genres: [],
  aliases: [],
  birth_date: null,
  death_date: null,
  external_identities: [],
};

const populatedOverview: PerformerOverview = {
  id: 'performer-1',
  name: 'Charlie Parker',
  biography: 'Alto saxophonist.',
  primary_image: {
    id: 'img-1',
    url: 'https://example.com/bird.jpg',
    alt_text: 'Portrait',
    width: 100,
    height: 100,
    attribution_text: 'Photo credit',
    attribution_url: null,
  },
  genres: [{ id: 'jazz', name: 'Jazz' }],
  aliases: ['Bird', 'Yardbird'],
  birth_date: { year: 1920, precision: 'exact_year' },
  death_date: { year: 1955, precision: 'circa_year' },
  external_identities: [
    {
      provider: 'MusicBrainz',
      identifier: 'mbid-1',
      url: 'https://musicbrainz.org/artist/mbid-1',
    },
    { provider: 'Discogs', identifier: 'bird', url: null },
    { provider: 'Wiki', identifier: 'x', url: 'javascript:alert(1)' },
  ],
};

describe('PerformerPageContent', () => {
  it('renders optional aliases, dates, biography, identities, genres, and image', async () => {
    const OriginalImage = window.Image;
    class SucceedingImage {
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      set src(_value: string) {
        queueMicrotask(() => this.onload?.());
      }
    }
    window.Image = SucceedingImage as unknown as typeof Image;

    renderWithProviders(<PerformerPageContent performer={populatedOverview} />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Charlie Parker' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Также известен как: Bird, Yardbird'),
    ).toBeInTheDocument();
    expect(screen.getByText('Родился: 1920')).toBeInTheDocument();
    expect(screen.getByText('Умер: ок. 1955')).toBeInTheDocument();
    expect(screen.getByText('Alto saxophonist.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Жанры' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Jazz' })).toHaveAttribute(
      'href',
      '/genres/jazz',
    );
    expect(
      screen.getByRole('heading', { name: 'Внешние идентификаторы' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'MusicBrainz: mbid-1' }),
    ).toHaveAttribute('href', 'https://musicbrainz.org/artist/mbid-1');
    expect(screen.getByText('Discogs: bird').closest('a')).toBeNull();
    expect(screen.getByText('Wiki: x').closest('a')).toBeNull();

    await waitFor(() => {
      expect(screen.getByRole('img', { name: 'Portrait' })).toHaveAttribute(
        'src',
        'https://example.com/bird.jpg',
      );
    });
    expect(screen.getByText('Photo credit')).toBeInTheDocument();

    window.Image = OriginalImage;
  });

  it('omits empty optional sections from the DOM', () => {
    renderWithProviders(<PerformerPageContent performer={emptyOverview} />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Count Basie' }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Также известен как/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Родился:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Умер:/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Жанры' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Внешние идентификаторы' }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
