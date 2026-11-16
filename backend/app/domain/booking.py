"""What a booking is: how its reference looks and how a passenger name is written."""

import secrets

# No 0/O or 1/I/L: references are read out over the phone and at the bus park.
REFERENCE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
REFERENCE_LENGTH = 8
PASSENGER_NAME_MAX_LENGTH = 120  # Booking.passenger_name column


def new_reference() -> str:
    """8 random characters: about 850 billion combinations, not guessable like an id."""
    return "".join(secrets.choice(REFERENCE_ALPHABET) for _ in range(REFERENCE_LENGTH))


def normalize_passenger_name(name: str) -> str:
    """Names go on the manifest in capitals, as on ID cards, single-spaced.

    The driver and road checkpoints read the manifest at a glance, and the same
    passenger is never stored twice as "Ada Obi" and "ada  obi".
    """
    return " ".join(name.split()).upper()
