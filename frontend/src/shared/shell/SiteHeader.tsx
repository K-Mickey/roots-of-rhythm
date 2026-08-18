import { Anchor, Box, Container, Group } from '@mantine/core';

const PRODUCT_NAME = 'Roots of Rhythm';

export function SiteHeader() {
  return (
    <Box
      component="header"
      bg="pastel.3"
      style={{ boxShadow: 'var(--mantine-shadow-xs)' }}
    >
      <Container size="52rem" py="md">
        <Group justify="space-between">
          <Anchor href="#" c="pastel.9" underline="hover" fw={600}>
            {PRODUCT_NAME}
          </Anchor>
        </Group>
      </Container>
    </Box>
  );
}
