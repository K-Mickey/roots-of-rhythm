import { Anchor, Container, Stack, Text, Title } from '@mantine/core';

export default function GenreNotFound() {
  return (
    <Container size="52rem" py="xl">
      <Stack gap="md">
        <Title order={1}>Материал не найден</Title>
        <Text>
          Запрошенная страница жанра отсутствует или недоступна для просмотра.
        </Text>
        <Anchor href="/" underline="hover">
          На главную
        </Anchor>
      </Stack>
    </Container>
  );
}
