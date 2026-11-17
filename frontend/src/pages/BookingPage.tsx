import { Alert, Box, Button, Container, Group, Loader, Stack, Text, Title } from '@mantine/core';

import { BookingForm } from '../components/booking/BookingForm';
import { BookingTicket } from '../components/booking/BookingTicket';
import { SearchBar } from '../components/booking/SearchBar';
import { TripRow } from '../components/booking/TripRow';
import { useBookingFlow } from '../hooks/useBookingFlow';
import { useBookingForm } from '../hooks/useBookingForm';
import { useTicketDownload } from '../hooks/useTicketDownload';
import { formatMoney } from '../lib/format';

/** Customer view: hooks hold the state and logic; this file only arranges the components. */
export function BookingPage() {
  const flow = useBookingFlow();
  const form = useBookingForm({
    trip: flow.selectedTrip, fare: flow.result?.fare ?? null,
    onBooked: flow.booked, onSeatsChanged: flow.refreshTrips,
  });
  const ticket = useTicketDownload(`ticket-${flow.confirmation?.reference}.png`);
  const { result } = flow;

  return (
    <>
      <Box bg="navy.9" pb={70} pt="xl">
        <Container size="lg">
          <Title c="white" order={1}>Where are you travelling?</Title>
          <Text c="gray.4" mt={4}>Intercity buses between Lagos, Ibadan, Enugu, Onitsha, Abuja and Kano.</Text>
        </Container>
      </Box>
      <Container size="lg" mt={-50} pb="xl">
        <SearchBar towns={flow.towns} values={flow.values} check={flow.check} minDate={flow.minDate}
          loading={flow.loading} onChange={flow.setValues} onSearch={flow.search} onClear={flow.clear} />

        {flow.error && <Alert color="red" mt="lg">{flow.error}</Alert>}
        {!result && !flow.error && !flow.confirmation && (
          <Text c="dimmed" ta="center" mt={48}>
            Choose where you are travelling from and to, then search to see departures, fares and seats left.
          </Text>
        )}
        {flow.confirmation && (
          <BookingTicket booking={flow.confirmation} ticketRef={ticket.ref}
            downloading={ticket.downloading} onDownload={ticket.download}
            action={<Button onClick={flow.dismissConfirmation}>Book another trip</Button>} />
        )}

        {result && (
          <Stack mt="xl" gap="sm">
            <Group justify="space-between">
              <Title order={3}>{result.origin.name} to {result.destination.name}</Title>
              <Text c="dimmed" size="sm">
                Zone {result.origin.zone} to Zone {result.destination.zone}: {formatMoney(result.fare)} per seat
              </Text>
            </Group>
            {flow.loading && <Loader size="sm" />}
            {!flow.loading && result.trips.length === 0 && (
              <Alert color="gray">
                No trips on this route {flow.values.date ? 'on this date' : 'coming up'}. Try another date, or
                clear the date to see every upcoming trip.
              </Alert>
            )}
            {result.trips.map((trip) => (
              <TripRow key={trip.id} trip={trip} fare={result.fare}
                selected={trip.id === flow.selectedTrip?.id} onSelect={() => flow.selectTrip(trip.id)}>
                {trip.id === flow.selectedTrip?.id && (
                  <BookingForm name={form.name} seats={form.seats} seatsAvailable={trip.seats_available}
                    total={form.total} check={form.check} error={form.error} submitting={form.submitting}
                    onNameChange={form.setName} onSeatsChange={form.setSeats} onSubmit={form.submit} />
                )}
              </TripRow>
            ))}
          </Stack>
        )}
      </Container>
    </>
  );
}
