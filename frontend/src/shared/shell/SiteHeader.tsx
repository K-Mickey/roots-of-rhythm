import { Anchor, Box, Container, Group } from '@mantine/core';

import { PRODUCT_NAME } from './product';

export function SiteHeader() {
  return (
    <Box
      component="header"
      bg="pastel.3"
      style={{ boxShadow: 'var(--mantine-shadow-xs)' }}
    >
      <Container fluid px="md" py="md">
        <Group justify="space-between" wrap="nowrap">
          <Group gap="md" wrap="nowrap">
            <Anchor href="/" c="pastel.9" underline="hover" fw={600}>
              {PRODUCT_NAME}
            </Anchor>
            <Anchor href="/genres" c="pastel.9" underline="hover">
              Жанры
            </Anchor>
            <Anchor href="/performers" c="pastel.9" underline="hover">
              Исполнители
            </Anchor>
          </Group>
        </Group>
      </Container>
    </Box>
  );
}
