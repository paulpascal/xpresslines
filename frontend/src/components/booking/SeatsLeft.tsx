import { Group, Progress, Stack, Text } from '@mantine/core';

import { seatsState, type SeatsLevel } from '../../lib/seats';

const COLORS: Record<SeatsLevel, string> = { plenty: 'teal', few: 'orange', soldOut: 'red' };

/** Seats left as the headline, with how full the bus is underneath. */
export function SeatsLeft({ available, capacity }: { available: number; capacity: number }) {
  const { booked, percentBooked, level } = seatsState(available, capacity);
  const color = COLORS[level];
  return (
    <Stack gap={4} w={150}>
      <Group gap={6} align="baseline" wrap="nowrap">
        <Text fw={800} fz={22} lh={1} c={`${color}.7`} className="numbers">
          {level === 'soldOut' ? 'Sold out' : available}
        </Text>
        {level !== 'soldOut' && (
          <Text size="sm" c={level === 'few' ? 'orange.7' : 'dimmed'} fw={level === 'few' ? 700 : 400}>
            {level === 'few' ? `seat${available > 1 ? 's' : ''} left!` : 'seats left'}
          </Text>
        )}
      </Group>
      <Progress value={percentBooked} color={color} size={6} radius="xl"
        aria-label={`${booked} of ${capacity} seats booked`} />
      <Text size="xs" c="dimmed" className="numbers">{booked} of {capacity} booked</Text>
    </Stack>
  );
}
