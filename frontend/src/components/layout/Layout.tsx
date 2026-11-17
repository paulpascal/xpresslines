import { Anchor, Box, Container, Group, Text } from '@mantine/core';
import { IconBus } from '@tabler/icons-react';
import type { ReactNode } from 'react';

const LINKS = [
  { key: 'book', href: '/', label: 'Book a trip' },
  { key: 'admin', href: '/admin', label: 'Operator dashboard' },
  { key: 'docs', href: '/api/v1/docs/swagger', label: 'API docs' },
] as const;

export type Page = 'book' | 'admin';

export function Layout({ active, children }: { active: Page; children: ReactNode }) {
  return (
    <Box bg="gray.0" mih="100vh">
      <Box bg="navy.9" py="md">
        <Container size="lg">
          <Group justify="space-between">
            <Group gap="xs">
              <IconBus color="var(--mantine-color-gold-5)" size={28} />
              <Text c="white" fw={800} size="lg">XpressLines</Text>
            </Group>
            <Group gap="lg">
              {LINKS.map((link) => (
                <Anchor
                  key={link.key}
                  href={link.href}
                  c={active === link.key ? 'gold.4' : 'gray.3'}
                  fw={active === link.key ? 700 : 500}
                  underline="never"
                >
                  {link.label}
                </Anchor>
              ))}
            </Group>
          </Group>
        </Container>
      </Box>
      {children}
    </Box>
  );
}
