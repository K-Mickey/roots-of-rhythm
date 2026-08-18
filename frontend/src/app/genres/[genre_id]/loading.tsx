import { Container, Skeleton, Stack, VisuallyHidden } from '@mantine/core';

export default function GenreLoading() {
  return (
    <Container
      size="52rem"
      py="xl"
      aria-busy="true"
      aria-live="polite"
      aria-label="Загрузка страницы жанра"
    >
      <VisuallyHidden>Загрузка страницы жанра</VisuallyHidden>
      <Stack gap="md">
        <Skeleton height={36} width="40%" />
        <Skeleton height={16} width="25%" />
        <Skeleton height={80} />
        <Skeleton height={24} width="30%" mt="md" />
        <Skeleton height={100} />
        <Skeleton height={100} />
      </Stack>
    </Container>
  );
}
