import { useEffect, useState } from 'react';

import { api, ApiError } from '../api/client';
import type { Booking, Money, Trip } from '../api/types';
import { multiplyMoney } from '../lib/format';
import { checkBooking, toManifestName } from '../lib/validation';

interface Options {
  trip: Trip | null;
  fare: Money | null;
  onBooked: (booking: Booking) => void;
  onSeatsChanged: () => void; // someone else booked first
}

/** The booking form's state, its rules and the call to the API. */
export function useBookingForm({ trip, fare, onBooked, onSeatsChanged }: Options) {
  const [name, setNameValue] = useState('');
  const [seats, setSeatsValue] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // One key per booking intent: resubmitting the same details reuses it (a safe
  // retry); changing the details is a new intent, so it gets a new key.
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());

  useEffect(() => {
    // A different trip is a fresh form.
    setNameValue('');
    setSeatsValue(1);
    setError(null);
    setIdempotencyKey(crypto.randomUUID());
  }, [trip?.id]);

  const check = checkBooking(name, seats, trip?.seats_available ?? 0);

  function setName(value: string) {
    setNameValue(toManifestName(value));
    setIdempotencyKey(crypto.randomUUID());
  }

  function setSeats(value: number) {
    setSeatsValue(value);
    setIdempotencyKey(crypto.randomUUID());
  }

  async function submit() {
    if (!trip || !check.canBook) return;
    setSubmitting(true);
    setError(null);
    try {
      onBooked(await api.book({ trip_id: trip.id, passenger_name: name, seats }, idempotencyKey));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong');
      if (e instanceof ApiError && e.code === 'not_enough_seats') onSeatsChanged();
    } finally {
      setSubmitting(false);
    }
  }

  return {
    name, setName, seats, setSeats, check, error, submitting, submit,
    total: fare ? multiplyMoney(fare, seats) : null,
  };
}
