import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { createAppTheme } from '@/shared/theme/theme';
import { AppShell } from '@/shared/shell/AppShell';

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

describe('AppShell', () => {
  it('exposes header, main, and footer landmarks', () => {
    renderWithProviders(
      <AppShell>
        <h1>Content</h1>
      </AppShell>,
    );

    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Roots of Rhythm' }),
    ).toHaveAttribute('href', '#');
    expect(screen.getByText(/© \d{4}/)).toBeInTheDocument();
  });
});
