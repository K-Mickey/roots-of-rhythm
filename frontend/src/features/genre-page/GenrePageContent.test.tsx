import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import type { GenreOverview } from '@/shared/api/genre';
import { createAppTheme } from '@/shared/theme/theme';

import { GenreImage } from './GenreImage';
import { GenrePageContent } from './GenrePageContent';
import { PageError } from './PageError';

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

const retryHref = '/genres/genre-1';

const baseOverview: GenreOverview = {
  id: 'genre-1',
  name: 'Swing',
  definition: 'Jazz-derived dance music.',
  primary_image: null,
  period: { label: '1930s', start: null, end: null },
  geography_or_origin: { summary: 'United States' },
  historical_context: 'Big bands and dance halls.',
  formation: 'Grew from earlier jazz practice.',
  characteristic_features: ['Swing feel', 'Dance orientation'],
};

describe('GenrePageContent', () => {
  it('renders populated overview, relations, and sources', () => {
    renderWithProviders(
      <GenrePageContent
        overview={baseOverview}
        retryHref={retryHref}
        relations={{
          status: 'ok',
          data: {
            genre_id: 'genre-1',
            relations: [
              {
                id: 'rel-1',
                related_genre: { id: 'jazz', name: 'Jazz' },
                relation_type: 'developed_from',
                perspective: 'subject',
                explanation: 'Swing developed from Jazz.',
                temporal_context: {
                  label: 'late 1920s–1930s',
                  start: null,
                  end: null,
                },
                geographic_context: { summary: 'United States' },
                evidence_status: 'supported',
                evidence_references: [
                  {
                    source_id: 'src-1',
                    role: 'supports',
                    locator_text: 'essay',
                    external_url: 'https://example.com/jazz',
                  },
                ],
              },
              {
                id: 'rel-2',
                related_genre: { id: 'jump', name: 'Jump Blues' },
                relation_type: 'contributed_to_emergence_of',
                perspective: 'subject',
                explanation: 'Swing contributed to Jump Blues.',
                temporal_context: {
                  label: 'late 1930s–1940s',
                  start: null,
                  end: null,
                },
                geographic_context: { summary: 'United States' },
                evidence_status: 'supported',
                evidence_references: [],
              },
            ],
          },
        }}
        sources={{
          status: 'ok',
          data: {
            genre_id: 'genre-1',
            sources: [
              {
                id: 'src-1',
                title: 'Jazz',
                author: null,
                responsible_organization: 'Smithsonian Music',
                publication: null,
                publication_date: null,
                external_url: 'https://example.com/jazz',
              },
            ],
          },
        }}
      />,
    );

    expect(
      screen.getByRole('heading', { level: 1, name: 'Swing' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Jazz-derived dance music.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Связи' })).toBeInTheDocument();
    expect(screen.getByText('Развился из — Jazz')).toBeInTheDocument();
    expect(
      screen.getByText('Участвовал в формировании — Jump Blues'),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText('Подтверждено источниками').length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole('heading', { name: 'Источники' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/\[1\] Jazz/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '[1]' })).toHaveAttribute(
      'href',
      '#source-src-1',
    );
  });

  it('omits empty optional sections from the DOM', () => {
    renderWithProviders(
      <GenrePageContent
        overview={{
          ...baseOverview,
          period: null,
          geography_or_origin: null,
          historical_context: null,
          formation: null,
          characteristic_features: [],
        }}
        retryHref={retryHref}
        relations={{
          status: 'ok',
          data: { genre_id: 'genre-1', relations: [] },
        }}
        sources={{ status: 'ok', data: { genre_id: 'genre-1', sources: [] } }}
      />,
    );

    expect(
      screen.queryByRole('heading', { name: 'Связи' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Источники' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Исторический контекст' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Характерные черты' }),
    ).not.toBeInTheDocument();
  });

  it('keeps overview visible when relations and sources fail', () => {
    renderWithProviders(
      <GenrePageContent
        overview={baseOverview}
        retryHref={retryHref}
        relations={{ status: 'error', message: 'relations down' }}
        sources={{ status: 'error', message: 'sources down' }}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Swing' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Связи' })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Источники' }),
    ).toBeInTheDocument();
    expect(screen.getByText('relations down')).toBeInTheDocument();
    expect(screen.getByText('sources down')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Повторить' })).toHaveLength(2);
    expect(
      screen.getAllByRole('link', { name: 'Повторить' })[0],
    ).toHaveAttribute('href', retryHref);
  });
});

describe('PageError', () => {
  it('renders page error with retry link', () => {
    renderWithProviders(
      <PageError
        message="Не удалось загрузить материал."
        retryHref={retryHref}
      />,
    );

    expect(
      screen.getByRole('heading', { name: 'Не удалось загрузить материал' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Повторить' })).toHaveAttribute(
      'href',
      retryHref,
    );
  });
});

describe('GenreImage', () => {
  it('does not render an img when the source fails to load', async () => {
    const OriginalImage = window.Image;
    class FailingImage {
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      set src(_value: string) {
        queueMicrotask(() => this.onerror?.());
      }
    }
    window.Image = FailingImage as unknown as typeof Image;

    renderWithProviders(
      <GenreImage
        image={{
          id: 'img-1',
          url: 'https://example.com/missing.jpg',
          alt_text: 'Poster',
          width: 100,
          height: 100,
          attribution_text: 'Photo credit',
          attribution_url: null,
        }}
      />,
    );

    expect(
      screen.queryByRole('img', { name: 'Poster' }),
    ).not.toBeInTheDocument();
    await waitFor(() => {
      expect(
        screen.queryByRole('img', { name: 'Poster' }),
      ).not.toBeInTheDocument();
      expect(screen.queryByText('Photo credit')).not.toBeInTheDocument();
    });

    window.Image = OriginalImage;
  });
});
