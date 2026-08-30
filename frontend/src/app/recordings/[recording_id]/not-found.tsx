import { Container, Stack, Text, Title } from '@mantine/core';

export default function RecordingNotFound() {
  return (
    <Container size="72rem" py="xl">
      <Stack>
        <Title order={1}>Запись не найдена</Title>
        <Text>Возможно, она не опубликована или была удалена.</Text>
      </Stack>
    </Container>
  );
}
