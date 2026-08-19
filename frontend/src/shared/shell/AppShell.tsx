import { Box } from '@mantine/core';
import type { ReactNode } from 'react';

import { SiteFooter } from './SiteFooter';
import { SiteHeader } from './SiteHeader';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <Box
      bg="pastel.1"
      c="pastel.9"
      style={{
        minHeight: '100vh',
        display: 'grid',
        // Grid keeps main a block container, so page Containers stay full width,
        // while the 1fr row gives them a height to center against.
        gridTemplateRows: 'auto 1fr auto',
      }}
    >
      <SiteHeader />
      <Box component="main">{children}</Box>
      <SiteFooter />
    </Box>
  );
}
