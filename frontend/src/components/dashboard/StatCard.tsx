import { Paper, Text } from '@mantine/core';

export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Paper withBorder p="md">
      <Text c="dimmed" size="xs" tt="uppercase" fw={700}>{label}</Text>
      <Text fw={800} fz={28} c="navy.9">{value}</Text>
    </Paper>
  );
}
