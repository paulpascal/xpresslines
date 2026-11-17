import { expect, it } from 'vitest';

import { formatMoney, formatTime, multiplyMoney, vehicle } from '../../src/lib/format';

it('shows times in Lagos, whatever the viewer timezone', () => {
  expect(formatTime('2026-11-20T13:30:00Z')).toBe('14:30');
});

it('multiplies money without floating-point noise', () => {
  expect(multiplyMoney({ amount: '25.00', currency: 'USD' }, 3)).toEqual({ amount: '75.00', currency: 'USD' });
  expect(formatMoney({ amount: '35.00', currency: 'USD' })).toBe('$35');
});

it('names the vehicle from its size', () => {
  expect([7, 15, 30, 50].map(vehicle)).toEqual(['Shared car', 'Minibus', 'Midibus', 'Coach']);
});
