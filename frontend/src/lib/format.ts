import type { Money, TripStatus } from '../api/types';

// The operator runs on Nigerian time, whatever the viewer's timezone.
const TZ = 'Africa/Lagos';

export const formatTime = (iso: string) =>
  new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit' }).format(new Date(iso));

export const formatDay = (iso: string) =>
  new Intl.DateTimeFormat('en-GB', { timeZone: TZ, weekday: 'short', day: 'numeric', month: 'short' }).format(new Date(iso));

export const formatMoney = ({ amount, currency }: Money) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 0 }).format(Number(amount));

export const multiplyMoney = (money: Money, times: number): Money => ({
  ...money,
  amount: (Number(money.amount) * times).toFixed(2),
});

export const todayInLagos = () =>
  new Intl.DateTimeFormat('en-CA', { timeZone: TZ }).format(new Date()); // YYYY-MM-DD

export const STATUS_LABELS: Record<TripStatus, string> = {
  scheduled: 'Scheduled',
  boarding: 'Boarding',
  departed: 'Departed',
  in_transit: 'In transit',
  arrived: 'Arrived',
  completed: 'Completed',
};

// Nigerian intercity fleets: Sienna shared cars, Hiace minibuses, Coaster midibuses, coaches.
export const vehicle = (seats: number) =>
  seats <= 8 ? 'Shared car' : seats <= 18 ? 'Minibus' : seats <= 35 ? 'Midibus' : 'Coach';
