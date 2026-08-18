import '@mantine/core/styles.css';

import { ColorSchemeScript, mantineHtmlProps } from '@mantine/core';
import type { Metadata } from 'next';
import { Source_Sans_3 } from 'next/font/google';
import type { ReactNode } from 'react';

import { AppShell } from '@/shared/shell/AppShell';
import { AppProviders } from '@/shared/theme/AppProviders';

const sourceSans = Source_Sans_3({
  subsets: ['latin', 'cyrillic'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Roots of Rhythm',
  description: 'История развития музыки и её связей',
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru" {...mantineHtmlProps} className={sourceSans.className}>
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <AppProviders fontFamily={sourceSans.style.fontFamily}>
          <AppShell>{children}</AppShell>
        </AppProviders>
      </body>
    </html>
  );
}
