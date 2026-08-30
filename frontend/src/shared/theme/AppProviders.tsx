'use client';

import { MantineProvider } from '@mantine/core';
import type { ReactNode } from 'react';

import { createAppTheme } from '@/shared/theme/theme';

export function AppProviders({
  children,
  fontFamily,
}: Readonly<{
  children: ReactNode;
  fontFamily: string;
}>) {
  const theme = createAppTheme(fontFamily);

  return <MantineProvider theme={theme}>{children}</MantineProvider>;
}
