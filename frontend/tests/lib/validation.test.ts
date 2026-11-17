import { describe, expect, it } from 'vitest';

import { checkBooking, checkSearch, toManifestName } from '../../src/lib/validation';

const TODAY = '2026-11-20';

describe('checkSearch', () => {
  it('needs both towns before searching', () => {
    expect(checkSearch({ origin: 'LOS', destination: '', date: TODAY }, TODAY).canSearch).toBe(false);
  });

  it('refuses the same town as origin and destination', () => {
    const check = checkSearch({ origin: 'LOS', destination: 'LOS', date: TODAY }, TODAY);
    expect(check.sameTown).toBe(true);
    expect(check.canSearch).toBe(false);
  });

  it('refuses a past date but accepts today and no date', () => {
    expect(checkSearch({ origin: 'LOS', destination: 'ABV', date: '2026-11-19' }, TODAY).pastDate).toBe(true);
    expect(checkSearch({ origin: 'LOS', destination: 'ABV', date: TODAY }, TODAY).canSearch).toBe(true);
    expect(checkSearch({ origin: 'LOS', destination: 'ABV', date: '' }, TODAY).canSearch).toBe(true);
  });

  it('knows when there is nothing to clear', () => {
    expect(checkSearch({ origin: '', destination: '', date: '' }, TODAY).isEmpty).toBe(true);
  });
});

describe('checkBooking', () => {
  it('needs a name of at least 2 characters', () => {
    expect(checkBooking(' A ', 1, 5).nameTooShort).toBe(true);
    expect(checkBooking('ADA', 1, 5).canBook).toBe(true);
  });

  it('accepts 1 to the seats left, whole numbers only', () => {
    expect(checkBooking('ADA', 0, 5).seatsInvalid).toBe(true);
    expect(checkBooking('ADA', 6, 5).seatsInvalid).toBe(true);
    expect(checkBooking('ADA', 1.5, 5).seatsInvalid).toBe(true);
    expect(checkBooking('ADA', 5, 5).canBook).toBe(true);
  });
});

it('writes names in capitals, as on the manifest', () => {
  expect(toManifestName('ada obi')).toBe('ADA OBI');
});
