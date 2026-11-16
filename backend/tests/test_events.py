"""Side effects subscribe to domain events instead of living in the booking code."""

import pytest

from app.domain import errors, events
from app.domain.lifecycle import TripStatus
from app.domain.models import Trip

from .conftest import make_services


@pytest.fixture
def bus_and_received():
    bus, received = events.EventBus(), []
    for event_type in events.ALL_EVENTS:
        bus.subscribe(event_type, received.append)
    return bus, received


def test_a_booking_announces_itself_after_commit(session, make_trip, bus_and_received):
    bus, received = bus_and_received
    trip = make_trip(capacity=7, seats_booked=4)
    booking = make_services(events=bus).booking(session).book(trip_id=trip.id, passenger_name="Ada", seats=2).booking
    assert received == [events.BookingCreated(booking.reference, trip.id, 2, booking.total_fare, 1)]


def test_refusals_and_status_changes_are_announced_too(session, make_trip, bus_and_received):
    bus, received = bus_and_received
    services = make_services(events=bus)
    trip = make_trip(capacity=7, seats_booked=7)
    with pytest.raises(errors.NotEnoughSeats):
        services.booking(session).book(trip_id=trip.id, passenger_name="Ada", seats=1)
    services.trips(session).change_status(trip.id, TripStatus.BOARDING)

    assert [type(e) for e in received] == [events.BookingRejected, events.TripStatusChanged]
    assert received[0].reason == "not_enough_seats"


def test_a_failing_subscriber_never_undoes_a_booking(session, make_trip):
    def broken_sms_gateway(event):
        raise ConnectionError("SMS provider down")

    bus = events.EventBus()
    bus.subscribe(events.BookingCreated, broken_sms_gateway)
    trip = make_trip()
    result = make_services(events=bus).booking(session).book(trip_id=trip.id, passenger_name="Ada", seats=1)
    assert result.created and session.get(Trip, trip.id).seats_booked == 1
