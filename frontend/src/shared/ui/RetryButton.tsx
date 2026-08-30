import { Button } from '@mantine/core';

export function RetryButton({
  href,
  label = 'Повторить',
}: Readonly<{
  href: string;
  label?: string;
}>) {
  return (
    <Button component="a" href={href} variant="default">
      {label}
    </Button>
  );
}
