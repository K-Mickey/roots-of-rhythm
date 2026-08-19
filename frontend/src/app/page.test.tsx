import { MantineProvider } from '@mantine/core';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PRODUCT_NAME, PRODUCT_TAGLINE } from '@/shared/shell/product';

import HomePage from './page';

describe('HomePage', () => {
  it('renders centered product name and tagline without genre links', () => {
    render(
      <MantineProvider>
        <HomePage />
      </MantineProvider>,
    );

    expect(
      screen.getByRole('heading', { name: PRODUCT_NAME }),
    ).toBeInTheDocument();
    expect(screen.getByText(PRODUCT_TAGLINE)).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByText(/Jazz|Swing|Jump Blues/)).not.toBeInTheDocument();
  });
});
