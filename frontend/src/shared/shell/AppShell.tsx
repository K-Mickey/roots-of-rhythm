import { Box } from '@mantine/core';
import type { ReactNode } from 'react';

import { SiteFooter } from './SiteFooter';
import { SiteHeader } from './SiteHeader';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <Box
      bg="pastel.1"
      c="pastel.9"
      style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}
    >
      <SiteHeader />
      <Box component="main" style={{ flex: 1 }}>
        {children}
      </Box>
      <SiteFooter />
    </Box>
  );
}
