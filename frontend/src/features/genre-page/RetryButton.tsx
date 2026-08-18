import { Button } from '@mantine/core';

export function RetryButton({
  href,
  label = 'Повторить',
}: {
  href: string;
  label?: string;
}) {
  return (
    <Button component="a" href={href} variant="default">
      {label}
    </Button>
  );
}
