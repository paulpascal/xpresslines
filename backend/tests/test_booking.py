from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.domain import errors
from app.domain.booking import REFERENCE_ALPHABET
from app.domain.lifecycle import TripStatus
from app.domain.models import Booking, Trip
from app.domain.pricing import ZoneFareTable

from .conftest import NOW, booking_service


def book(session, trip, seats=1, name="Ada Obi", **kwargs):
    return booking_service(session).book(trip_id=trip.id, passenger_name=name, seats=seats, **kwargs)


def test_booking_returns_a_reference_and_snapshots_the_fare(session, make_trip):
    trip = make_trip("LOS", "KAN")
    result = book(session, trip, seats=3, name="  Adébáyọ̀   Obi  ")

    booking = result.booking
    assert result.created
    assert len(booking.reference) == 8 and set(booking.reference) <= set(REFERENCE_ALPHABET)
    assert booking.passenger_name == "ADÉBÁYỌ̀ OBI"  # manifest style: capitals, single spaces
    assert booking.unit_fare == Decimal("35.00")
    assert booking.total_fare == Decimal("105.00")
    assert session.get(Trip, trip.id).seats_booked == 3


def test_booking_exactly_the_last_seats_succeeds(session, make_trip):
    trip = make_trip(capacity=14, seats_booked=12)
    book(session, trip, seats=2)
    assert session.get(Trip, trip.id).seats_available == 0


def test_booking_one_seat_more_than_available_is_refused(session, make_trip):
    trip = make_trip(capacity=14, seats_booked=12)
    with pytest.raises(errors.NotEnoughSeats) as refused:
        book(session, trip, seats=3)
    assert refused.value.details["seats_available"] == 2
    assert session.get(Trip, trip.id).seats_booked == 12  # nothing changed


def test_sold_out_trip_is_refused(session, make_trip):
    trip = make_trip(capacity=14, seats_booked=14)
    with pytest.raises(errors.NotEnoughSeats, match="sold out"):
        book(session, trip)


@pytest.mark.parametrize("seats", [0, -1])
def test_zero_or_negative_seats_are_refused(session, make_trip, seats):
    trip = make_trip()
    with pytest.raises(errors.InvalidRequest):
        book(session, trip, seats=seats)


def test_blank_name_is_refused(session, make_trip):
    with pytest.raises(errors.InvalidRequest):
        book(session, make_trip(), name="   ")


@pytest.mark.parametrize("status", [s for s in TripStatus if s != TripStatus.SCHEDULED])
def test_only_scheduled_trips_take_bookings(session, make_trip, status):
    trip = make_trip(status=status)
    with pytest.raises(errors.TripNotBookable):
        book(session, trip)


def test_trip_still_marked_scheduled_after_its_departure_time_is_refused(session, make_trip):
    # The operator forgot to update the status: the clock still wins.
    trip = make_trip(departs_at=NOW - timedelta(minutes=1))
    with pytest.raises(errors.TripNotBookable, match="already left"):
        book(session, trip)


def test_unknown_trip(session, towns):
    with pytest.raises(errors.TripNotFound):
        booking_service(session).book(trip_id=999, passenger_name="Ada", seats=1)


def test_retry_with_the_same_idempotency_key_returns_the_same_booking(session, make_trip):
    trip = make_trip()
    first = book(session, trip, seats=2, idempotency_key="key-1")
    retry = book(session, trip, seats=2, idempotency_key="key-1")

    assert retry.created is False
    assert retry.booking.reference == first.booking.reference
    assert session.get(Trip, trip.id).seats_booked == 2  # charged once


def test_same_idempotency_key_for_a_different_booking_is_refused(session, make_trip):
    trip = make_trip()
    book(session, trip, seats=2, idempotency_key="key-1")
    with pytest.raises(errors.IdempotencyConflict):
        book(session, trip, seats=5, idempotency_key="key-1")


def test_seat_counter_always_matches_the_sum_of_bookings(session, make_trip):
    trip = make_trip(capacity=10)
    for seats in (3, 4, 2):
        book(session, trip, seats=seats)
    with pytest.raises(errors.NotEnoughSeats):
        book(session, trip, seats=2)

    total = session.scalar(select(func.sum(Booking.seats)).where(Booking.trip_id == trip.id))
    assert session.get(Trip, trip.id).seats_booked == total == 9


def test_database_refuses_overbooking_even_if_code_is_bypassed(session, make_trip):
    trip = make_trip(capacity=14, seats_booked=14)
    with pytest.raises(IntegrityError, match="seats_within_capacity"):
        session.execute(text("UPDATE trips SET seats_booked = 15 WHERE id = :id"), {"id": trip.id})
    session.rollback()


def test_lookup_booking_by_reference_is_case_insensitive(session, make_trip):
    reference = book(session, make_trip()).booking.reference
    assert booking_service(session).get(reference.lower()).reference == reference
    with pytest.raises(errors.BookingNotFound):
        booking_service(session).get("NOPE2345")


def test_drift_check_flags_a_counter_written_outside_the_service(session, make_trip):
    from app.cli.checks import seat_counter_drift

    trip = make_trip()
    book(session, trip, seats=2)
    assert seat_counter_drift(session) == []

    session.execute(text("UPDATE trips SET seats_booked = 5 WHERE id = :id"), {"id": trip.id})
    session.commit()
    assert seat_counter_drift(session) == [(trip.id, 5, 2)]


def test_retry_matches_the_name_however_it_was_typed(session, make_trip):
    # The rule applies before the idempotency comparison, so a retry that only
    # differs in case or spacing is the same booking, not a conflict.
    trip = make_trip()
    first = book(session, trip, name="Ada Obi", idempotency_key="key-1")
    retry = book(session, trip, name="ADA  OBI", idempotency_key="key-1")
    assert retry.created is False and retry.booking.reference == first.booking.reference


def test_a_new_booking_rule_is_one_function(session, make_trip):
    # Rule chain: e.g. the operator caps a booking at 6 seats. No booking code changes.
    from app.domain.booking_rules import DEFAULT_BOOKING_RULES

    def at_most_six_seats(trip, seats, now):
        if seats > 6:
            raise errors.InvalidRequest("At most 6 seats per booking")

    service = booking_service(session, booking_rules=(*DEFAULT_BOOKING_RULES, at_most_six_seats))
    trip = make_trip()
    with pytest.raises(errors.InvalidRequest, match="At most 6"):
        service.book(trip_id=trip.id, passenger_name="Ada", seats=7)
    assert service.book(trip_id=trip.id, passenger_name="Ada", seats=6).created

def test_rows_inserted_outside_the_app_get_safe_database_defaults(session, towns):
    # Migration 0002: a raw SQL insert (ops script, data fix) still gets a valid trip.
    session.execute(text(
        "INSERT INTO trips (origin_id, destination_id, departs_at, capacity) "
        "VALUES (:o, :d, now() + interval '1 day', 15)"
    ), {"o": towns["LOS"].id, "d": towns["ABV"].id})
    session.commit()
    trip = session.scalar(select(Trip))
    assert (trip.seats_booked, trip.status) == (0, TripStatus.SCHEDULED)


def test_a_new_fare_policy_reprices_new_bookings_only(session, make_trip):
    # Pricing is a strategy injected into the service: a peak-season policy is a
    # new class, the booking code is untouched, and past bookings keep their price.
    class PeakSeason:
        def __init__(self, base, surcharge):
            self.base, self.surcharge = base, surcharge

        def fare(self, zone_a, zone_b):
            return self.base.fare(zone_a, zone_b) + self.surcharge

    trip = make_trip("LOS", "ABV")
    before = booking_service(session).book(trip_id=trip.id, passenger_name="Ada", seats=1).booking
    peak = booking_service(session, pricing=PeakSeason(ZoneFareTable(), Decimal("5.00")))
    after = peak.book(trip_id=trip.id, passenger_name="Obi", seats=1).booking

    assert (before.unit_fare, after.unit_fare) == (Decimal("25.00"), Decimal("30.00"))
    session.refresh(before)
    assert before.unit_fare == Decimal("25.00")  # history untouched
