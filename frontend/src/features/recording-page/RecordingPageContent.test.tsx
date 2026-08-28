import { MantineProvider } from '@mantine/core';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import type { RecordingOverview } from '@/shared/api/recording';
import { createAppTheme } from '@/shared/theme/theme';

import { RecordingPageContent } from './RecordingPageContent';

it('renders recording links, machine and fallback labels, and hides empty sections', () => {
  const recording: RecordingOverview = {
    id: 'recording-1',
    title: 'Take Five',
    period: { start: null, end: null },
    description: null,
    isrc: null,
    first_release_date: null,
    origin_badges: [],
    genres: [],
    listening_guide: null,
    works: [
      {
        work: { id: 'work-1', name: 'Take Five' },
        usage_kind: 'complete',
        position: null,
      },
    ],
    credits: [
      {
        target_kind: 'group',
        target: { id: 'group-1', name: 'Dave Brubeck Quartet' },
        billing_role: 'primary',
        contribution_kind: null,
        instrument: null,
        credited_as: null,
      },
    ],
    lyrics: [
      {
        id: 'lyrics-1',
        language_tag: 'ru',
        label: null,
        creation_method: 'machine_translation',
        body: 'Текст',
        body_unavailable_reason: null,
        position: null,
        confirmed_for_recording: false,
      },
    ],
  };
  render(
    <MantineProvider theme={createAppTheme('sans-serif')}>
      <RecordingPageContent recording={recording} />
    </MantineProvider>,
  );
  expect(
    screen.getByRole('heading', { level: 1, name: 'Take Five' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Take Five' })).toHaveAttribute(
    'href',
    '/songs/work-1',
  );
  expect(screen.getByText('Машинный перевод')).toBeInTheDocument();
  expect(
    screen.getByText('Соответствие текста этой записи не подтверждено'),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('heading', { name: 'Жанры' }),
  ).not.toBeInTheDocument();
});

it('shows work usage kind for partial and medley usages', () => {
  const recording: RecordingOverview = {
    id: 'recording-2',
    title: 'Medley Night',
    period: { start: null, end: null },
    description: null,
    isrc: null,
    first_release_date: null,
    origin_badges: [],
    genres: [],
    listening_guide: null,
    lyrics: [],
    credits: [
      {
        target_kind: 'group',
        target: { id: 'group-1', name: 'Quartet' },
        billing_role: 'primary',
        contribution_kind: null,
        instrument: null,
        credited_as: null,
      },
    ],
    works: [
      {
        work: { id: 'work-1', name: 'Song A' },
        usage_kind: 'partial',
        position: null,
      },
      {
        work: { id: 'work-2', name: 'Song B' },
        usage_kind: 'medley_component',
        position: 1,
      },
      {
        work: { id: 'work-3', name: 'Song C' },
        usage_kind: 'complete',
        position: null,
      },
    ],
  };
  render(
    <MantineProvider theme={createAppTheme('sans-serif')}>
      <RecordingPageContent recording={recording} />
    </MantineProvider>,
  );
  expect(screen.getByText(/фрагмент:/)).toBeInTheDocument();
  expect(screen.getByText(/медли:/)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Song C' })).toBeInTheDocument();
  expect(screen.queryByText(/complete:/i)).not.toBeInTheDocument();
});
