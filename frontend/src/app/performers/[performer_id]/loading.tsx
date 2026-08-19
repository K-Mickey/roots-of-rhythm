import { Container, Skeleton, Stack, VisuallyHidden } from '@mantine/core';

export default function PerformerLoading() {
  return (
    <Container
      size="52rem"
      py="xl"
      aria-busy="true"
      aria-live="polite"
      aria-label="Загрузка страницы исполнителя"
    >
      <VisuallyHidden>Загрузка страницы исполнителя</VisuallyHidden>
      <Stack gap="md">
        <Skeleton height={36} width="40%" />
        <Skeleton height={80} />
        <Skeleton height={24} width="30%" mt="md" />
        <Skeleton height={60} />
      </Stack>
    </Container>
  );
}
