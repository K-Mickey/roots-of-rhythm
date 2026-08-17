import { Container, Stack, Text, Title } from '@mantine/core';

export default function HomePage() {
  return (
    <main>
      <Container py="xl">
        <Stack gap="sm">
          <Title>Roots of Rhythm</Title>
          <Text>История развития музыки и её связей.</Text>
        </Stack>
      </Container>
    </main>
  );
}
