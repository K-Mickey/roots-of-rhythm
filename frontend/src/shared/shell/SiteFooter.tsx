import { Box, Container, Group, Text } from '@mantine/core';

const PRODUCT_NAME = 'Roots of Rhythm';

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <Box component="footer" bg="pastel.2" mt="auto">
      <Container size="52rem" py="md">
        <Group gap="sm">
          <Text size="sm" c="pastel.9">
            {PRODUCT_NAME}
          </Text>
          <Text size="sm" c="pastel.8">
            © {year}
          </Text>
        </Group>
      </Container>
    </Box>
  );
}
