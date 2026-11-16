from datetime import date, datetime, timedelta

import pytest

from app.config import OPERATOR_TZ
from app.domain import errors
from app.domain.lifecycle import TripStatus

from .conftest import NOW, trip_service


def test_search_returns_the_zone_fare_and_upcoming_trips_in_time_order(session, make_trip):
    later = make_trip(departs_at=NOW + timedelta(days=2))
    sooner = make_trip(departs_at=NOW + timedelta(hours=3))
    make_trip("LOS", "KAN")  # other route

    quote, trips = trip_service(session).search("LOS", "ABV")

    assert str(quote.unit_fare) == "25.00"
    assert [t.id for t in trips] == [sooner.id, later.id]


def test_search_hides_trips_that_left_or_no_longer_sell(session, make_trip):
    make_trip(departs_at=NOW - timedelta(hours=1))
    make_trip(status=TripStatus.BOARDING)
    make_trip(status=TripStatus.DEPARTED)
    _, trips = trip_service(session).search("LOS", "ABV")
    assert trips == []


def test_sold_out_trips_are_shown_with_zero_seats(session, make_trip):
    make_trip(capacity=14, seats_booked=14)
    _, trips = trip_service(session).search("LOS", "ABV")
    assert [t.seats_available for t in trips] == [0]


def test_date_means_the_calendar_day_in_lagos_not_utc(session, make_trip):
    # 00:30 in Lagos on 25 Nov is still 24 Nov in UTC.
    just_after_midnight = datetime(2026, 11, 25, 0, 30, tzinfo=OPERATOR_TZ)
    trip = make_trip(departs_at=just_after_midnight)
    past_now = datetime(2026, 11, 1, tzinfo=OPERATOR_TZ)

    _, on_25th = trip_service(session, clock=lambda: past_now).search("LOS", "ABV", date(2026, 11, 25))
    _, on_24th = trip_service(session, clock=lambda: past_now).search("LOS", "ABV", date(2026, 11, 24))

    assert [t.id for t in on_25th] == [trip.id]
    assert on_24th == []


def test_same_origin_and_destination_is_refused(session, towns):
    with pytest.raises(errors.InvalidRequest):
        trip_service(session).search("LOS", "los")


def test_unknown_town_is_refused(session, towns):
    with pytest.raises(errors.TownNotFound):
        trip_service(session).search("LOS", "XXX")


def test_towns_in_the_same_zone_pay_the_intra_zone_fare(session, towns):
    quote, _ = trip_service(session).search("LOS", "IBA")
    assert str(quote.unit_fare) == "8.00"
