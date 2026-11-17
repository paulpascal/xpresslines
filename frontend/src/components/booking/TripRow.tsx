import { Button, Group, Paper, Stack, Text } from '@mantine/core';
import { IconArrowRight } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import type { Money, Trip } from '../../api/types';
import { formatDay, formatMoney, formatTime, vehicle } from '../../lib/format';
import { SeatsLeft } from './SeatsLeft';

interface Props {
  trip: Trip;
  fare: Money;
  selected: boolean;
  onSelect: () => void;
  children?: ReactNode; // the inline booking form, when selected
}

export function TripRow({ trip, fare, selected, onSelect, children }: Props) {
  const soldOut = trip.seats_available === 0;
  return (
    <Paper withBorder p="md" shadow={selected ? 'sm' : undefined}
      style={{ borderColor: selected ? 'var(--mantine-color-navy-6)' : undefined }}>
      <Group justify="space-between" wrap="nowrap">
        <Group gap="xl" wrap="nowrap">
          <Stack gap={0} w={90}>
            <Text fw={800} size="xl" className="numbers">{formatTime(trip.departs_at)}</Text>
            <Text c="dimmed" size="sm">{formatDay(trip.departs_at)}</Text>
          </Stack>
          <Stack gap={4}>
            <Group gap={6}>
              <Text fw={600}>{trip.origin.name}</Text>
              <IconArrowRight size={16} color="var(--mantine-color-gray-5)" />
              <Text fw={600}>{trip.destination.name}</Text>
            </Group>
            <Text c="dimmed" size="sm">
              {vehicle(trip.capacity)}, {trip.capacity} seats
            </Text>
          </Stack>
        </Group>
        <Group gap="xl" wrap="nowrap">
          <SeatsLeft available={trip.seats_available} capacity={trip.capacity} />
          <Stack gap={0} align="flex-end" w={70}>
            <Text fw={800} size="xl" c="navy.9" className="numbers">{formatMoney(fare)}</Text>
            <Text c="dimmed" size="xs">per seat</Text>
          </Stack>
          <Button color="gold" c="navy.9" disabled={soldOut} onClick={onSelect}
            variant={selected ? 'light' : 'filled'} w={100}>
            {selected ? 'Selected' : 'Select'}
          </Button>
        </Group>
      </Group>
      {children}
    </Paper>
  );
}
