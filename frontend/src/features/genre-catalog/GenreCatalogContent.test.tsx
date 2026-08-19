import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { createAppTheme } from '@/shared/theme/theme';

import { GenreCatalogContent } from './GenreCatalogContent';

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

describe('GenreCatalogContent', () => {
  it('renders published genre names as detail links', () => {
    renderWithProviders(
      <GenreCatalogContent
        items={[
          { id: 'jazz', name: 'Jazz' },
          { id: 'jump', name: 'Jump Blues' },
          { id: 'swing', name: 'Swing' },
        ]}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Жанры' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /^Jazz$/ })).toHaveAttribute(
      'href',
      '/genres/jazz',
    );
    expect(screen.getByRole('link', { name: /^Jump Blues$/ })).toHaveAttribute(
      'href',
      '/genres/jump',
    );
    expect(screen.getByRole('link', { name: /^Swing$/ })).toHaveAttribute(
      'href',
      '/genres/swing',
    );
  });

  it('keeps the heading when the list is empty', () => {
    renderWithProviders(<GenreCatalogContent items={[]} />);

    expect(screen.getByRole('heading', { name: 'Жанры' })).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
