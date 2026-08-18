import { Container, Stack, Text, Title } from '@mantine/core';

export default function HomePage() {
  return (
    <Container size="52rem" py="xl">
      <Stack gap="sm">
        <Title order={1}>Roots of Rhythm</Title>
        <Text>История развития музыки и её связей.</Text>
      </Stack>
    </Container>
  );
}
