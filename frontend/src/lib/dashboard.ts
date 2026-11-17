// Operator dashboard figures. Pure functions: no React.

import type { DashboardTrip, TripStatus } from '../api/types';

export type StatusFilter = TripStatus | 'all';

export interface DashboardStats {
  seatsSold: number;
  loadFactorPercent: number | null; // null when there is no capacity to divide by
  onTheRoad: number;
}

export function dashboardStats(trips: DashboardTrip[]): DashboardStats {
  const seatsSold = trips.reduce((sum, t) => sum + t.seats_booked, 0);
  const capacity = trips.reduce((sum, t) => sum + t.capacity, 0);
  return {
    seatsSold,
    loadFactorPercent: capacity ? Math.round((100 * seatsSold) / capacity) : null,
    onTheRoad: trips.filter((t) => t.status === 'departed' || t.status === 'in_transit').length,
  };
}

export const filterByStatus = (trips: DashboardTrip[], filter: StatusFilter) =>
  filter === 'all' ? trips : trips.filter((t) => t.status === filter);

// A full upcoming trip is an alert; a full trip that already left is good news.
export const isSoldOutAlert = (trip: DashboardTrip) =>
  trip.seats_booked === trip.capacity && trip.status === 'scheduled';
