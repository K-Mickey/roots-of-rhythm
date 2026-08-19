import { Alert, Stack, Text, Title } from '@mantine/core';

import { RetryButton } from './RetryButton';

export function PageError({
  message,
  retryHref,
}: {
  message: string;
  retryHref: string;
}) {
  return (
    <Stack gap="md" py="xl">
      <Title order={1}>Не удалось загрузить материал</Title>
      <Alert color="red" title="Ошибка">
        <Text>{message}</Text>
      </Alert>
      <RetryButton href={retryHref} />
    </Stack>
  );
}
