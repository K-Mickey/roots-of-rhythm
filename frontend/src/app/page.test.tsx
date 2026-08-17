import { MantineProvider } from '@mantine/core';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import HomePage from './page';

describe('HomePage', () => {
  it('renders the project identity', () => {
    render(
      <MantineProvider>
        <HomePage />
      </MantineProvider>,
    );

    expect(
      screen.getByRole('heading', { name: 'Roots of Rhythm' }),
    ).toBeInTheDocument();
  });
});
