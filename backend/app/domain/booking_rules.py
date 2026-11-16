"""Rules a booking must pass, checked in order on the locked trip (rule chain).

Each rule is a small function that raises a DomainError to refuse. A new rule
(sales close 30 minutes before departure, at most 6 seats per booking...) is
one more function in DEFAULT_BOOKING_RULES; the booking code does not change.
"""

from collections.abc import Callable
from datetime import datetime

from . import errors
from .lifecycle import TripStatus
from .models import Trip

BookingRule = Callable[[Trip, int, datetime], None]


def trip_is_on_sale(trip: Trip, seats: int, now: datetime) -> None:
    if trip.status != TripStatus.SCHEDULED:
        raise errors.TripNotBookable(
            f"This trip is {trip.status.label.lower()} and no longer takes bookings",
            trip_id=trip.id, status=trip.status.value,
        )


def trip_has_not_left(trip: Trip, seats: int, now: datetime) -> None:
    # The clock wins over a status someone forgot to update.
    if trip.departs_at <= now:
        raise errors.TripNotBookable("This trip has already left", trip_id=trip.id)


def enough_seats_left(trip: Trip, seats: int, now: datetime) -> None:
    left = trip.seats_available
    if seats > left:
        raise errors.NotEnoughSeats(
            "This trip is sold out" if left == 0
            else f"Only {left} seat{'s' if left > 1 else ''} left on this trip",
            trip_id=trip.id, seats_requested=seats, seats_available=left,
        )


DEFAULT_BOOKING_RULES: tuple[BookingRule, ...] = (trip_is_on_sale, trip_has_not_left, enough_seats_left)
