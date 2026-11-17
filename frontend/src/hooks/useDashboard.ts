import { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../api/client';
import type { DashboardPage, DashboardTrip, TripStatus } from '../api/types';
import { dashboardStats, filterByStatus, type StatusFilter } from '../lib/dashboard';

export const REFRESH_MS = 10_000;
const PAGE_SIZE = 50;

/** Operator dashboard: all trips page by page, refreshed on their own, with status changes. */
export function useDashboard() {
  const [page, setPage] = useState<DashboardPage | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [error, setError] = useState<string | null>(null);
  const [busyTripId, setBusyTripId] = useState<number | null>(null);

  const load = useCallback(() => {
    api.dashboardTrips((pageNumber - 1) * PAGE_SIZE, PAGE_SIZE)
      .then((p) => { setPage(p); setError(null); })
      .catch(() => setError('Cannot load trips. Is the API running?'));
  }, [pageNumber]);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_MS); // new bookings show up on their own
    return () => clearInterval(timer);
  }, [load]);

  async function advance(trip: DashboardTrip, to: TripStatus) {
    setBusyTripId(trip.id);
    try {
      const updated = await api.changeStatus(trip.id, to);
      setPage((p) => p && { ...p, trips: p.trips.map((t) => (t.id === updated.id ? updated : t)) });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not update the trip');
    } finally {
      setBusyTripId(null);
    }
  }

  const trips = page?.trips ?? [];
  return {
    total: page?.total ?? 0,
    pageCount: page ? Math.ceil(page.total / page.limit) : 0,
    pageNumber, setPageNumber,
    filter, setFilter,
    visibleTrips: filterByStatus(trips, filter),
    stats: dashboardStats(trips),
    error, busyTripId, advance,
  };
}
