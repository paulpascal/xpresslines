import { expect, it } from 'vitest';

import { seatsState } from '../../src/lib/seats';

it('describes how full a bus is', () => {
  expect(seatsState(40, 50)).toEqual({ booked: 10, percentBooked: 20, level: 'plenty' });
  expect(seatsState(3, 7).level).toBe('few');
  expect(seatsState(0, 7).level).toBe('soldOut');
});
