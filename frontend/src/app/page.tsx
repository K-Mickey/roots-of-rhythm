import { Box, Container, Stack, Text, Title } from '@mantine/core';

import { PRODUCT_NAME, PRODUCT_TAGLINE } from '@/shared/shell/product';

export default function HomePage() {
  return (
    <Box
      style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 0,
      }}
    >
      <Container size="52rem" py="xl">
        <Stack align="center" gap="sm">
          <Title order={1} ta="center">
            {PRODUCT_NAME}
          </Title>
          <Text ta="center" size="lg">
            {PRODUCT_TAGLINE}
          </Text>
        </Stack>
      </Container>
    </Box>
  );
}
