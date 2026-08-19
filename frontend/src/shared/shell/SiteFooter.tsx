import { Box, Container, Text } from '@mantine/core';

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <Box component="footer" bg="pastel.2" mt="auto">
      <Container fluid px="md" py="md">
        <Text size="sm" c="pastel.8" ta="center">
          © {year}
        </Text>
      </Container>
    </Box>
  );
}
