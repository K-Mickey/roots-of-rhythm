import type { ReactElement } from 'react';

import { MantineProvider } from '@mantine/core';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { createAppTheme } from '@/shared/theme/theme';

import { GroupCatalogContent } from './GroupCatalogContent';

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

describe('GroupCatalogContent', () => {
  it('renders published group names as detail links', () => {
    renderWithProviders(
      <GroupCatalogContent
        items={[
          { id: 'group-1', name: 'Benny Goodman Orchestra' },
          { id: 'group-2', name: 'Count Basie Orchestra' },
        ]}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Группы' })).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /^Benny Goodman Orchestra$/ }),
    ).toHaveAttribute('href', '/groups/group-1');
    expect(
      screen.getByRole('link', { name: /^Count Basie Orchestra$/ }),
    ).toHaveAttribute('href', '/groups/group-2');
  });

  it('keeps the heading when the list is empty', () => {
    renderWithProviders(<GroupCatalogContent items={[]} />);

    expect(screen.getByRole('heading', { name: 'Группы' })).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
