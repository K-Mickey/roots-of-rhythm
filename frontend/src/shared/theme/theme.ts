import { createTheme, type MantineColorsTuple } from '@mantine/core';

const pastel: MantineColorsTuple = [
  '#FFFFFF',
  '#F7FAFC',
  '#DDE5EB',
  '#C5D0D8',
  '#A8B6C2',
  '#8A9AAB',
  '#6B7C8F',
  '#3D5A73',
  '#2F4558',
  '#1B242C',
];

export function createAppTheme(fontFamily: string) {
  return createTheme({
    primaryColor: 'pastel',
    colors: { pastel },
    defaultRadius: 0,
    fontFamily,
    headings: {
      fontFamily,
      fontWeight: '600',
    },
    shadows: {
      xs: '0 1px 2px rgba(27, 36, 44, 0.06)',
      sm: '0 1px 3px rgba(27, 36, 44, 0.08)',
    },
  });
}
