"""Booking seats: safe under concurrency and safe to retry."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..domain import errors
from ..domain.booking import PASSENGER_NAME_MAX_LENGTH, new_reference, normalize_passenger_name
from ..domain.booking_rules import BookingRule
from ..domain.clock import Clock
from ..domain.events import BookingCreated, BookingRejected, EventBus
from ..domain.models import Booking, Trip
from ..domain.pricing import CURRENCY, FarePolicy, total_fare
from ..infra.db import committing
from .locking import lock_trip

log = logging.getLogger(__name__)

MAX_BOOKING_ATTEMPTS = 3
IDEMPOTENCY_KEY_MAX_LENGTH = 64


@dataclass(frozen=True)
class BookingResult:
    booking: Booking
    created: bool  # False when an idempotent retry returned an existing booking


class BookingService:
    def __init__(
        self,
        session: Session,
        pricing: FarePolicy,
        rules: Sequence[BookingRule],
        clock: Clock,
        events: EventBus,
    ) -> None:
        self.session = session
        self.pricing = pricing
        self.rules = rules
        self.clock = clock
        self.events = events

    def book(
        self, *, trip_id: int, passenger_name: str, seats: int, idempotency_key: str | None = None
    ) -> BookingResult:
        """Book seats on a trip.

        The trip row is locked (SELECT ... FOR UPDATE) for the few milliseconds of
        the check-and-write, so two customers racing for the last seat are served
        one after the other: the second one sees the updated count and is refused.
        """
        passenger_name = normalize_passenger_name(passenger_name)
        self._validate(passenger_name, seats, idempotency_key)

        # A retry of a booking already saved needs no lock: answer it at once,
        # even if the key comes with another trip that is busy.
        if idempotency_key and (existing := self._find_by_key(idempotency_key)):
            return self._replay(existing, trip_id, passenger_name, seats)

        for attempt in range(1, MAX_BOOKING_ATTEMPTS + 1):
            try:
                with committing(self.session):
                    trip = lock_trip(self.session, trip_id)
                    # Checked under the lock: if a duplicate of this request was
                    # in flight, it has committed by now and we return its booking
                    # instead of refusing a "sold out" trip the customer already holds.
                    if idempotency_key and (existing := self._find_by_key(idempotency_key)):
                        return self._replay(existing, trip_id, passenger_name, seats)
                    booking = self._create(trip, passenger_name, seats, idempotency_key)
                    # Built before the commit, sent after it: once the booking is
                    # saved, nothing can fail on a database read.
                    created = BookingCreated(
                        booking.reference, trip_id, seats, booking.total_fare, trip.seats_available,
                    )
            except IntegrityError:
                # Either the same idempotency key committed in parallel (return
                # that booking) or a reference collided (retry with a new one).
                if idempotency_key and (existing := self._find_by_key(idempotency_key)):
                    return self._replay(existing, trip_id, passenger_name, seats)
                if attempt == MAX_BOOKING_ATTEMPTS:
                    raise
                continue

            self.events.publish(created)
            return BookingResult(booking, created=True)
        raise AssertionError("unreachable")

    def get(self, reference: str) -> Booking:
        if not (reference.isascii() and reference.isalnum()):  # never send junk to the database
            raise errors.BookingNotFound("No booking with this reference", reference=reference)
        booking = self.session.scalar(
            select(Booking)
            .options(joinedload(Booking.trip).joinedload(Trip.origin),
                     joinedload(Booking.trip).joinedload(Trip.destination))
            .where(Booking.reference == reference.upper())
        )
        if booking is None:
            raise errors.BookingNotFound("No booking with this reference", reference=reference)
        return booking

    # Internals

    @staticmethod
    def _validate(passenger_name: str, seats: int, idempotency_key: str | None) -> None:
        # Repeated from the HTTP schema on purpose: other channels call this service too.
        if seats < 1:
            raise errors.InvalidRequest("Book at least one seat", seats=seats)
        if not passenger_name:
            raise errors.InvalidRequest("Passenger name is required")
        if len(passenger_name) > PASSENGER_NAME_MAX_LENGTH:  # after capitals: "ß" becomes "SS"
            raise errors.InvalidRequest(f"Passenger name is longer than {PASSENGER_NAME_MAX_LENGTH} characters")
        if idempotency_key and len(idempotency_key) > IDEMPOTENCY_KEY_MAX_LENGTH:
            raise errors.InvalidRequest(f"Idempotency-Key must be at most {IDEMPOTENCY_KEY_MAX_LENGTH} characters")

    def _create(self, trip: Trip, passenger_name: str, seats: int, idempotency_key: str | None) -> Booking:
        """Check the rules on the locked trip, then write the booking."""
        try:
            for rule in self.rules:
                rule(trip, seats, self.clock())
        except errors.DomainError as refusal:
            self.events.publish(BookingRejected(trip.id, refusal.code, refusal.details))
            raise

        unit_fare = self.pricing.fare(trip.origin.zone, trip.destination.zone)
        trip.seats_booked += seats
        booking = Booking(
            reference=new_reference(),
            trip=trip,
            passenger_name=passenger_name,
            seats=seats,
            unit_fare=unit_fare,
            total_fare=total_fare(unit_fare, seats),
            currency=CURRENCY,
            idempotency_key=idempotency_key,
            created_at=self.clock(),
        )
        self.session.add(booking)
        self.session.flush()  # surface unique-constraint errors inside the transaction
        return booking

    def _find_by_key(self, key: str) -> Booking | None:
        return self.session.scalar(select(Booking).where(Booking.idempotency_key == key))

    @staticmethod
    def _replay(existing: Booking, trip_id: int, passenger_name: str, seats: int) -> BookingResult:
        if (existing.trip_id, existing.passenger_name, existing.seats) != (trip_id, passenger_name, seats):
            raise errors.IdempotencyConflict("This Idempotency-Key was already used for a different booking")
        log.info("booking_replayed", extra={"fields": {"reference": existing.reference}})
        return BookingResult(existing, created=False)
