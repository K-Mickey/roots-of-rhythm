import { Alert, Stack, Text, Title } from '@mantine/core';

import { RetryButton } from './RetryButton';

export function SectionError({
  title,
  message,
  retryHref,
}: {
  title: string;
  message: string;
  retryHref: string;
}) {
  return (
    <Stack
      gap="sm"
      component="section"
      aria-labelledby={`section-error-${title}`}
    >
      <Title order={2} id={`section-error-${title}`}>
        {title}
      </Title>
      <Alert color="red" title="Ошибка загрузки">
        <Stack gap="sm">
          <Text>{message}</Text>
          <RetryButton href={retryHref} />
        </Stack>
      </Alert>
    </Stack>
  );
}
