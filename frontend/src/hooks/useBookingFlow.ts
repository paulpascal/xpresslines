import { useEffect, useState } from 'react';

import { api, ApiError } from '../api/client';
import type { Booking, SearchResult, Town } from '../api/types';
import { todayInLagos } from '../lib/format';
import { checkSearch, type SearchValues } from '../lib/validation';

const EMPTY_SEARCH: SearchValues = { origin: '', destination: '', date: '' };

/** Everything the booking page does: search, pick a trip, show the confirmation. */
export function useBookingFlow() {
  const [towns, setTowns] = useState<Town[]>([]);
  const [values, setValues] = useState<SearchValues>({ ...EMPTY_SEARCH, date: todayInLagos() });
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTripId, setSelectedTripId] = useState<number | null>(null);
  const [confirmation, setConfirmation] = useState<Booking | null>(null);

  useEffect(() => {
    api.towns().then(setTowns).catch(() => setError('Cannot load towns. Is the API running?'));
  }, []);

  const fetchTrips = () => api.searchTrips(values.origin, values.destination, values.date || undefined);

  async function search() {
    setLoading(true);
    setError(null);
    setSelectedTripId(null);
    setConfirmation(null);
    try {
      setResult(await fetchTrips());
    } catch (e) {
      setResult(null);
      setError(e instanceof ApiError ? e.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  // Someone else booked first: refresh seat counts without closing the open form.
  async function refreshTrips() {
    const fresh = await fetchTrips().catch(() => null);
    if (fresh) setResult(fresh);
  }

  function clear() {
    setValues(EMPTY_SEARCH);
    setResult(null);
    setError(null);
    setSelectedTripId(null);
    setConfirmation(null);
  }

  function selectTrip(tripId: number) {
    setSelectedTripId(tripId);
    setConfirmation(null);
  }

  function booked(booking: Booking) {
    setConfirmation(booking);
    setSelectedTripId(null);
    // Show the new seat count straight away.
    setResult((r) => r && { ...r, trips: r.trips.map((t) => (t.id === booking.trip.id ? booking.trip : t)) });
  }

  return {
    towns, values, setValues, check: checkSearch(values, todayInLagos()), minDate: todayInLagos(),
    result, error, loading, search, refreshTrips, clear,
    selectedTrip: result?.trips.find((t) => t.id === selectedTripId) ?? null, selectTrip,
    confirmation, booked, dismissConfirmation: () => setConfirmation(null),
  };
}
