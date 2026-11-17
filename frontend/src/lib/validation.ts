// The same rules as the API, checked as the customer types. Pure functions: no React.

export interface SearchValues {
  origin: string;
  destination: string;
  date: string; // YYYY-MM-DD, or '' for every upcoming trip
}

export interface SearchCheck {
  sameTown: boolean;
  pastDate: boolean;
  canSearch: boolean;
  isEmpty: boolean;
}

export function checkSearch(values: SearchValues, today: string): SearchCheck {
  const incomplete = !values.origin || !values.destination;
  const sameTown = !incomplete && values.origin === values.destination;
  const pastDate = values.date !== '' && values.date < today; // ISO dates compare as strings
  return {
    sameTown,
    pastDate,
    canSearch: !incomplete && !sameTown && !pastDate,
    isEmpty: !values.origin && !values.destination && !values.date,
  };
}

export interface BookingCheck {
  nameTooShort: boolean;
  seatsInvalid: boolean;
  canBook: boolean;
}

export function checkBooking(name: string, seats: number, seatsAvailable: number): BookingCheck {
  const nameTooShort = name.trim().length < 2;
  const seatsInvalid = !Number.isInteger(seats) || seats < 1 || seats > seatsAvailable;
  return { nameTooShort, seatsInvalid, canBook: !nameTooShort && !seatsInvalid };
}

// Names go on the manifest in capitals, as on ID cards (the API stores them that way too).
export const toManifestName = (name: string) => name.toUpperCase();
