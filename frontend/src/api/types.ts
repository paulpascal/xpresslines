// Mirrors the JSON contract in backend/app/schemas.py.

export type TripStatus =
  | 'scheduled' | 'boarding' | 'departed' | 'in_transit' | 'arrived' | 'completed';

export interface Money { amount: string; currency: string }
export interface Town { code: string; name: string; zone: number }

export interface Trip {
  id: number;
  origin: Town;
  destination: Town;
  departs_at: string;
  capacity: number;
  seats_available: number;
  status: TripStatus;
}

export interface SearchResult {
  origin: Town;
  destination: Town;
  fare: Money;
  date: string | null;
  trips: Trip[];
}

export interface Booking {
  reference: string;
  passenger_name: string;
  seats: number;
  unit_fare: Money;
  total_fare: Money;
  created_at: string;
  trip: Trip;
}

export interface DashboardTrip extends Trip {
  seats_booked: number;
  bookings_count: number;
  next_status: TripStatus | null;
}

export interface DashboardPage {
  date_from: string | null;
  date_to: string | null;
  total: number;
  limit: number;
  offset: number;
  trips: DashboardTrip[];
}
