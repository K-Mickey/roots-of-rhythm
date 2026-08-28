import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { createAppTheme } from '@/shared/theme/theme';

import { SongCatalogContent } from './SongCatalogContent';

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

describe('SongCatalogContent', () => {
  it('renders published song names as detail links', () => {
    renderWithProviders(
      <SongCatalogContent
        items={[
          { id: 'song-1', name: 'Sixteen Tons' },
          { id: 'song-2', name: "One O'Clock Jump" },
        ]}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Песни' })).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /^Sixteen Tons$/ }),
    ).toHaveAttribute('href', '/songs/song-1');
    expect(
      screen.getByRole('link', { name: /^One O'Clock Jump$/ }),
    ).toHaveAttribute('href', '/songs/song-2');
  });

  it('keeps the heading when the list is empty', () => {
    renderWithProviders(<SongCatalogContent items={[]} />);

    expect(screen.getByRole('heading', { name: 'Песни' })).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
