import { Container, Skeleton, Stack } from '@mantine/core';

export default function Loading() {
  return (
    <Container size="52rem" py="xl">
      <Stack>
        <Skeleton height={42} width="60%" />
        <Skeleton height={120} />
      </Stack>
    </Container>
  );
}
