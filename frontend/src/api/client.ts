import type { Booking, DashboardPage, DashboardTrip, SearchResult, Town, TripStatus } from './types';

/** An error the API explained (code + human message), shown as-is to users. */
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
  } catch {
    throw new ApiError(0, 'network_error', 'Cannot reach the server. Check your connection and try again.');
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = body?.error;
    const field = error?.details?.fields?.[0];
    const message = field ? `${field.field}: ${field.message}` : error?.message;
    throw new ApiError(response.status, error?.code ?? 'unknown', message ?? 'Something went wrong');
  }
  return body as T;
}

export const api = {
  towns: () => request<Town[]>('/towns'),

  searchTrips: (origin: string, destination: string, date?: string) => {
    const params = new URLSearchParams({ origin, destination });
    if (date) params.set('date', date);
    return request<SearchResult>(`/trips?${params}`);
  },

  // The same key is re-sent if the customer retries, so a flaky connection
  // can never create two bookings.
  book: (body: { trip_id: number; passenger_name: string; seats: number }, idempotencyKey: string) =>
    request<Booking>('/bookings', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Idempotency-Key': idempotencyKey },
    }),

  // All trips, soonest first, one page at a time.
  dashboardTrips: (offset = 0, limit = 50) =>
    request<DashboardPage>(`/admin/trips?${new URLSearchParams({ offset: String(offset), limit: String(limit) })}`),

  changeStatus: (tripId: number, status: TripStatus) =>
    request<DashboardTrip>(`/admin/trips/${tripId}/status`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    }),
};
