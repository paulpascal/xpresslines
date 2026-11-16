"""What happens when several customers try to book the last seats at once?

Each thread uses its own database connection, like separate web requests.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy import func, select

from app.domain import errors
from app.domain.models import Booking, Trip

from .conftest import booking_service


def race(session_factory, trip_id, clients, seats=1, key=None):
    start = Barrier(clients)

    def attempt(n):
        with session_factory() as s:
            start.wait()  # everyone fires at the same moment
            try:
                result = booking_service(s).book(
                    trip_id=trip_id, passenger_name="Same Customer" if key else f"Customer {n}", seats=seats,
                    idempotency_key=key,
                )
                return result.booking.reference
            except errors.NotEnoughSeats:
                return "refused"

    with ThreadPoolExecutor(max_workers=clients) as pool:
        return list(pool.map(attempt, range(clients)))


def test_two_customers_one_last_seat(session, session_factory, make_trip):
    trip = make_trip(capacity=14, seats_booked=13)

    outcomes = race(session_factory, trip.id, clients=2)

    assert sorted(o == "refused" for o in outcomes) == [False, True]
    session.expire_all()
    assert session.get(Trip, trip.id).seats_booked == 14


def test_twenty_customers_five_seats(session, session_factory, make_trip):
    trip = make_trip(capacity=44, seats_booked=39)

    outcomes = race(session_factory, trip.id, clients=20)

    assert sum(o != "refused" for o in outcomes) == 5
    session.expire_all()
    assert session.get(Trip, trip.id).seats_booked == 44
    assert session.scalar(select(func.count(Booking.id))) == 5


def test_same_request_retried_in_parallel_books_once(session, session_factory, make_trip):
    # A flaky mobile connection: the app re-sends the same booking 5 times at once.
    trip = make_trip()

    outcomes = race(session_factory, trip.id, clients=5, seats=2, key="phone-retry-1")

    assert len(set(outcomes)) == 1  # everyone got the same reference
    session.expire_all()
    assert session.get(Trip, trip.id).seats_booked == 2


def test_double_click_on_the_last_seats_returns_the_booking_not_sold_out(session, session_factory, make_trip):
    # Both copies of the request want the last 2 seats. The first books them;
    # the second must get that same booking back, not "sold out".
    trip = make_trip(capacity=14, seats_booked=12)

    outcomes = race(session_factory, trip.id, clients=5, seats=2, key="double-click")

    assert "refused" not in outcomes and len(set(outcomes)) == 1
    session.expire_all()
    assert session.get(Trip, trip.id).seats_booked == 14
