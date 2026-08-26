import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import type { GroupOverview } from '@/shared/api/group';
import { createAppTheme } from '@/shared/theme/theme';

import { GroupPageContent } from './GroupPageContent';

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

const emptyOverview: GroupOverview = {
  id: 'group-1',
  name: 'Benny Goodman Orchestra',
  aliases: [],
  description: null,
  period: { start: null, end: null },
  primary_image: null,
  genres: [],
  members: [],
};

const populatedOverview: GroupOverview = {
  id: 'group-3',
  name: 'Count Basie Orchestra',
  aliases: ['Basie band'],
  description: 'A swing orchestra.',
  period: {
    start: { year: 1935, precision: 'exact_year' },
    end: { year: 1950, precision: 'circa_year' },
  },
  primary_image: null,
  genres: [{ id: 'swing', name: 'Swing' }],
  members: [
    {
      id: 'performer-1',
      name: 'Count Basie',
      period: {
        start: { year: 1935, precision: 'exact_year' },
        end: { year: 1950, precision: 'circa_year' },
      },
      roles_or_instruments: ['piano', 'bandleader'],
    },
  ],
};

describe('GroupPageContent', () => {
  it('renders optional aliases, description, period, genres, and members', () => {
    renderWithProviders(<GroupPageContent group={populatedOverview} />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'Count Basie Orchestra' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Также известна как: Basie band'),
    ).toBeInTheDocument();
    expect(screen.getByText('Период: 1935 — ок. 1950')).toBeInTheDocument();
    expect(screen.getByText('A swing orchestra.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Жанры' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Swing' })).toHaveAttribute(
      'href',
      '/genres/swing',
    );
    expect(
      screen.getByRole('heading', { name: 'Участники' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Count Basie' })).toHaveAttribute(
      'href',
      '/performers/performer-1',
    );
    expect(
      screen.getByText('(1935 — ок. 1950; piano, bandleader)'),
    ).toBeInTheDocument();
  });

  it('omits empty optional sections from the DOM', () => {
    renderWithProviders(<GroupPageContent group={emptyOverview} />);

    expect(
      screen.getByRole('heading', {
        level: 1,
        name: 'Benny Goodman Orchestra',
      }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Также известна как/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Период:/)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Жанры' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Участники' }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
