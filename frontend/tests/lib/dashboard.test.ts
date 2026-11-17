import { describe, expect, it } from 'vitest';

import type { DashboardTrip, TripStatus } from '../../src/api/types';
import { dashboardStats, filterByStatus, isSoldOutAlert } from '../../src/lib/dashboard';

const trip = (status: TripStatus, seats_booked: number, capacity: number): DashboardTrip => ({
  id: Math.random(), status, seats_booked, capacity, seats_available: capacity - seats_booked,
  bookings_count: 1, next_status: null, departs_at: '2026-11-20T08:00:00+01:00',
  origin: { code: 'LOS', name: 'Lagos', zone: 1 }, destination: { code: 'ABV', name: 'Abuja', zone: 3 },
});

describe('dashboardStats', () => {
  it('adds seats sold, load factor and trips on the road', () => {
    const stats = dashboardStats([trip('scheduled', 10, 50), trip('departed', 7, 7), trip('in_transit', 3, 15)]);
    expect(stats).toEqual({ seatsSold: 20, loadFactorPercent: 28, onTheRoad: 2 });
  });

  it('has no load factor without trips', () => {
    expect(dashboardStats([]).loadFactorPercent).toBeNull();
  });
});

it('filters trips by status', () => {
  const trips = [trip('scheduled', 0, 7), trip('arrived', 7, 7)];
  expect(filterByStatus(trips, 'all')).toHaveLength(2);
  expect(filterByStatus(trips, 'arrived').map((t) => t.status)).toEqual(['arrived']);
});

it('alerts only on sold-out trips that have not left', () => {
  expect(isSoldOutAlert(trip('scheduled', 7, 7))).toBe(true);
  expect(isSoldOutAlert(trip('departed', 7, 7))).toBe(false);
});
