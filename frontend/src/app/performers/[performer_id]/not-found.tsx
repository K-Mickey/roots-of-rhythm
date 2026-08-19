import { Anchor, Container, Stack, Text, Title } from '@mantine/core';

export default function PerformerNotFound() {
  return (
    <Container size="52rem" py="xl">
      <Stack gap="md">
        <Title order={1}>Материал не найден</Title>
        <Text>
          Запрошенная страница исполнителя отсутствует или недоступна для
          просмотра.
        </Text>
        <Anchor href="/" underline="hover">
          На главную
        </Anchor>
      </Stack>
    </Container>
  );
}
