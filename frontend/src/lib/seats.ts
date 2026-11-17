// How full a trip is, and how urgent to show it. Pure function: no React.

export const FEW_SEATS = 3;

export type SeatsLevel = 'plenty' | 'few' | 'soldOut';

export interface SeatsState {
  booked: number;
  percentBooked: number;
  level: SeatsLevel;
}

export function seatsState(available: number, capacity: number): SeatsState {
  const booked = capacity - available;
  const level: SeatsLevel = available === 0 ? 'soldOut' : available <= FEW_SEATS ? 'few' : 'plenty';
  return { booked, percentBooked: (100 * booked) / capacity, level };
}
