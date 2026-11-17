import { Badge, Button, CopyButton, Divider, Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import { IconArrowRight, IconCheck, IconCopy, IconDownload } from '@tabler/icons-react';
import type { ReactNode, Ref } from 'react';

import type { Booking } from '../../api/types';
import { formatDay, formatMoney, formatTime, vehicle } from '../../lib/format';

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <Text size="xs" c="dimmed" tt="uppercase" fw={700}>{label}</Text>
      <Text fw={600} className="numbers">{children}</Text>
    </div>
  );
}

interface Props {
  booking: Booking;
  ticketRef: Ref<HTMLDivElement>; // the element saved as an image
  downloading: boolean;
  onDownload: () => void;
  action?: ReactNode; // "Book another trip ?"
}

/** The confirmed booking, shown as a ticket. Buttons marked data-no-export stay out of the image. */
export function BookingTicket({ booking, ticketRef, downloading, onDownload, action }: Props) {
  const { trip } = booking;
  return (
    <Paper ref={ticketRef} withBorder radius="lg" p="lg" mt="md"
      style={{ borderTop: '6px solid var(--mantine-color-teal-6)' }}>
      <Group justify="space-between" align="flex-start">
        <div>
          <Group gap="xs">
            <Text fw={800} size="lg">Booking confirmed</Text>
            <Badge color="teal" variant="light">Confirmed</Badge>
          </Group>
          <Text size="sm" c="dimmed">XpressLines, booking reference</Text>
          <Group gap="xs" mt={4}>
            <Text ff="monospace" fw={800} fz={34} c="navy.9" lh={1.1} data-testid="booking-reference">
              {booking.reference}
            </Text>
            <CopyButton value={booking.reference}>
              {({ copied, copy }) => (
                <Button size="xs" variant="light" color={copied ? 'teal' : 'navy'} data-no-export
                  leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />} onClick={copy}>
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              )}
            </CopyButton>
          </Group>
        </div>
        <Stack gap={4} align="flex-end">
          <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Total</Text>
          <Text fw={800} fz={28} c="navy.9" className="numbers">{formatMoney(booking.total_fare)}</Text>
          <Text size="xs" c="dimmed" className="numbers">{booking.seats} x {formatMoney(booking.unit_fare)}</Text>
        </Stack>
      </Group>

      <Divider my="md" variant="dashed" />

      <Group gap={8} mb="md">
        <Text fw={800} size="xl">{trip.origin.name}</Text>
        <IconArrowRight size={18} color="var(--mantine-color-gray-5)" />
        <Text fw={800} size="xl">{trip.destination.name}</Text>
      </Group>
      <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="md">
        <Field label="Date">{formatDay(trip.departs_at)}</Field>
        <Field label="Departure (Lagos time)">{formatTime(trip.departs_at)}</Field>
        <Field label="Passenger">{booking.passenger_name}</Field>
        <Field label="Seats">{booking.seats}</Field>
        <Field label="Vehicle">{vehicle(trip.capacity)}, {trip.capacity} seats</Field>
        <Field label="Booked on">{formatDay(booking.created_at)}, {formatTime(booking.created_at)}</Field>
      </SimpleGrid>

      <Divider my="md" variant="dashed" />

      <Group justify="space-between">
        <Text size="sm" c="dimmed">Show this reference at the bus park when you board.</Text>
        <Group gap="xs" data-no-export>
          <Button color="gold" c="navy.9" leftSection={<IconDownload size={16} />} loading={downloading}
            onClick={onDownload}>
            Download ticket
          </Button>
          {action}
        </Group>
      </Group>
    </Paper>
  );
}
