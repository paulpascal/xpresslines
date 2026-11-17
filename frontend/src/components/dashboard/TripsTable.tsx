import { Button, Group, Paper, Progress, Table, Text } from '@mantine/core';
import { IconArrowRight } from '@tabler/icons-react';

import type { DashboardTrip, TripStatus } from '../../api/types';
import { isSoldOutAlert } from '../../lib/dashboard';
import { formatDay, formatTime, STATUS_LABELS } from '../../lib/format';
import { StatusBadge } from './StatusBadge';

interface Props {
  trips: DashboardTrip[];
  busyTripId: number | null;
  onAdvance: (trip: DashboardTrip, to: TripStatus) => void;
}

export function TripsTable({ trips, busyTripId, onAdvance }: Props) {
  return (
    <Paper withBorder>
      <Table verticalSpacing="sm" horizontalSpacing="md" highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Route</Table.Th>
            <Table.Th>Departure</Table.Th>
            <Table.Th>Capacity</Table.Th>
            <Table.Th w={220}>Bookings so far</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Next step</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {trips.map((trip) => (
            <Table.Tr key={trip.id}>
              <Table.Td>
                <Group gap={6} wrap="nowrap">
                  <Text fw={600}>{trip.origin.name}</Text>
                  <IconArrowRight size={14} color="var(--mantine-color-gray-5)" />
                  <Text fw={600}>{trip.destination.name}</Text>
                </Group>
              </Table.Td>
              <Table.Td>
                <Text fw={600}>{formatTime(trip.departs_at)}</Text>
                <Text c="dimmed" size="xs">{formatDay(trip.departs_at)}</Text>
              </Table.Td>
              <Table.Td>{trip.capacity}</Table.Td>
              <Table.Td>
                <Text size="sm" className="numbers"><b>{trip.seats_booked}</b> / {trip.capacity} seats</Text>
                <Progress value={(100 * trip.seats_booked) / trip.capacity} my={4} size="sm"
                  color={isSoldOutAlert(trip) ? 'red' : 'navy'} />
                <Text size="xs" c="dimmed" className="numbers">
                  {trip.bookings_count} booking{trip.bookings_count === 1 ? '' : 's'}
                </Text>
              </Table.Td>
              <Table.Td><StatusBadge status={trip.status} /></Table.Td>
              <Table.Td>
                {trip.next_status ? (
                  <Button size="xs" variant="light" loading={busyTripId === trip.id}
                    onClick={() => onAdvance(trip, trip.next_status!)}>
                    Mark {STATUS_LABELS[trip.next_status].toLowerCase()}
                  </Button>
                ) : <Text c="dimmed" size="sm">Done</Text>}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {trips.length === 0 && <Text c="dimmed" ta="center" p="lg">No trips with this status.</Text>}
    </Paper>
  );
}
