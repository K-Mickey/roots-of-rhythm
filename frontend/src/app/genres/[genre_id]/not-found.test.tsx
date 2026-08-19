import { MantineProvider } from '@mantine/core';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import GenreNotFound from './not-found';

describe('GenreNotFound', () => {
  it('links back to home', () => {
    render(
      <MantineProvider>
        <GenreNotFound />
      </MantineProvider>,
    );

    expect(screen.getByRole('link', { name: 'На главную' })).toHaveAttribute(
      'href',
      '/',
    );
  });
});
