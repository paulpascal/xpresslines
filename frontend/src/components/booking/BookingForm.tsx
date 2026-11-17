import { Alert, Button, Divider, Group, NumberInput, Text, TextInput } from '@mantine/core';

import type { Money } from '../../api/types';
import { formatMoney } from '../../lib/format';
import type { BookingCheck } from '../../lib/validation';

interface Props {
  name: string;
  seats: number;
  seatsAvailable: number;
  total: Money | null;
  check: BookingCheck;
  error: string | null;
  submitting: boolean;
  onNameChange: (name: string) => void;
  onSeatsChange: (seats: number) => void;
  onSubmit: () => void;
}

export function BookingForm(props: Props) {
  const { name, seats, seatsAvailable, total, check, error, submitting } = props;
  return (
    <form onSubmit={(e) => { e.preventDefault(); props.onSubmit(); }}>
      <Divider my="md" />
      <Group align="flex-start">
        <TextInput label="Passenger name (as on ID card)" placeholder="e.g. ADA OBI" required
          value={name} onChange={(e) => props.onNameChange(e.currentTarget.value)} style={{ flex: 1 }}
          error={name !== '' && check.nameTooShort ? 'At least 2 characters' : undefined} />
        <NumberInput label="Seats" min={1} max={seatsAvailable} required w={110}
          allowDecimal={false} allowNegative={false} clampBehavior="strict"
          error={check.seatsInvalid ? `1 to ${seatsAvailable}` : undefined}
          value={seats} onChange={(value) => props.onSeatsChange(Number(value) || 1)} />
        <Text fw={700} size="lg" w={110} ta="right" mt={30} className="numbers">
          {total && formatMoney(total)}
        </Text>
        <Button type="submit" loading={submitting} disabled={!check.canBook} mt={25}>
          Confirm booking
        </Button>
      </Group>
      {error && <Alert color="red" mt="md" title="Booking not made">{error}</Alert>}
    </form>
  );
}
