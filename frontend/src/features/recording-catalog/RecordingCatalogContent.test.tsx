import { MantineProvider } from '@mantine/core';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import type { RecordingList } from '@/shared/api/recording';
import { createAppTheme } from '@/shared/theme/theme';

import { RecordingCatalogContent } from './RecordingCatalogContent';

it('renders recording links with primary credits, period, and genres', () => {
  const items: RecordingList['items'] = [
    {
      id: 'recording-1',
      title: 'Take Five',
      period: {
        start: { year: 1959, precision: 'exact_year' },
        end: null,
      },
      primary_credits: [
        {
          target_kind: 'group',
          target: { id: 'group-1', name: 'Dave Brubeck Quartet' },
        },
      ],
      genres: [{ id: 'genre-1', name: 'Jazz' }],
    },
  ];
  render(
    <MantineProvider theme={createAppTheme('sans-serif')}>
      <RecordingCatalogContent items={items} />
    </MantineProvider>,
  );
  expect(
    screen.getByRole('heading', { level: 1, name: 'Записи' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Take Five' })).toHaveAttribute(
    'href',
    '/recordings/recording-1',
  );
  expect(
    screen.getByRole('link', { name: 'Dave Brubeck Quartet' }),
  ).toHaveAttribute('href', '/groups/group-1');
  expect(screen.getByText(/Период записи: 1959/)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Jazz' })).toHaveAttribute(
    'href',
    '/genres/genre-1',
  );
});
