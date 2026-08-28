import { MantineProvider } from '@mantine/core';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PRODUCT_NAME } from './product';
import { SiteHeader } from './SiteHeader';

describe('SiteHeader', () => {
  it('links identity home, genres catalog, and performers catalog', () => {
    render(
      <MantineProvider>
        <SiteHeader />
      </MantineProvider>,
    );

    expect(screen.getByRole('link', { name: PRODUCT_NAME })).toHaveAttribute(
      'href',
      '/',
    );
    expect(screen.getByRole('link', { name: 'Жанры' })).toHaveAttribute(
      'href',
      '/genres',
    );
    expect(screen.getByRole('link', { name: 'Исполнители' })).toHaveAttribute(
      'href',
      '/performers',
    );
    expect(screen.getByRole('link', { name: 'Группы' })).toHaveAttribute(
      'href',
      '/groups',
    );
    expect(screen.getByRole('link', { name: 'Песни' })).toHaveAttribute(
      'href',
      '/songs',
    );
  });
});
