"""Towns, fares and trips: what customers search and operators run."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..config import OPERATOR_TZ
from ..domain import errors
from ..domain.clock import Clock
from ..domain.events import EventBus, TripStatusChanged
from ..domain.lifecycle import TRIP_TRANSITIONS, TripStatus
from ..domain.models import Booking, Town, Trip
from ..domain.pricing import CURRENCY, FarePolicy
from ..infra.db import committing
from .locking import lock_trip

DASHBOARD_MAX_LIMIT = 100


@dataclass(frozen=True)
class Quote:
    origin: Town
    destination: Town
    unit_fare: Decimal
    currency: str = CURRENCY


@dataclass(frozen=True)
class DashboardRow:
    trip: Trip
    bookings_count: int


@dataclass(frozen=True)
class DashboardPage:
    rows: list[DashboardRow]
    total: int
    date_from: date | None
    date_to: date | None
    limit: int
    offset: int


def _lagos_midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=OPERATOR_TZ)


class TripService:
    def __init__(self, session: Session, pricing: FarePolicy, clock: Clock, events: EventBus) -> None:
        self.session = session
        self.pricing = pricing
        self.clock = clock
        self.events = events

    # Customers

    def towns(self) -> list[Town]:
        return list(self.session.scalars(select(Town).order_by(Town.zone, Town.name)))

    def town(self, code: str) -> Town:
        if not (code.isascii() and code.isalpha()):  # never send junk (e.g. NUL bytes) to the database
            raise errors.TownNotFound(f"Unknown town code '{code}'", code=code)
        town = self.session.scalar(select(Town).where(Town.code == code.upper()))
        if town is None:
            raise errors.TownNotFound(f"Unknown town code '{code}'", code=code)
        return town

    def quote(self, origin_code: str, destination_code: str) -> Quote:
        if origin_code.upper() == destination_code.upper():
            raise errors.InvalidRequest("Origin and destination must be different towns")
        origin, destination = self.town(origin_code), self.town(destination_code)
        return Quote(origin, destination, self.pricing.fare(origin.zone, destination.zone))

    def search(self, origin_code: str, destination_code: str, on_date: date | None = None) -> tuple[Quote, list[Trip]]:
        """Bookable trips on a route, optionally on one Lagos calendar day.

        Sold-out trips are included (seats_available == 0) so customers see them.
        """
        quote = self.quote(origin_code, destination_code)
        query = (
            select(Trip)
            .options(joinedload(Trip.origin), joinedload(Trip.destination))
            .where(
                Trip.origin_id == quote.origin.id,
                Trip.destination_id == quote.destination.id,
                Trip.status == TripStatus.SCHEDULED,
                Trip.departs_at > self.clock(),
            )
            .order_by(Trip.departs_at)
        )
        if on_date is not None:
            query = query.where(
                Trip.departs_at >= _lagos_midnight(on_date),
                Trip.departs_at < _lagos_midnight(on_date + timedelta(days=1)),
            )
        return quote, list(self.session.scalars(query))

    # Operators

    def dashboard(
        self,
        *,
        status: TripStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DashboardPage:
        """All trips, soonest first, one page at a time.

        Pagination keeps every response small whether the operator has 10 trips or
        a year of history; optional Lagos-day filters narrow the list further.
        """
        if date_from and date_to and date_to < date_from:
            raise errors.InvalidRequest("date_to must be on or after date_from")
        limit = min(limit, DASHBOARD_MAX_LIMIT)

        conditions = []
        if date_from is not None:
            conditions.append(Trip.departs_at >= _lagos_midnight(date_from))
        if date_to is not None:
            conditions.append(Trip.departs_at < _lagos_midnight(date_to + timedelta(days=1)))
        if status is not None:
            conditions.append(Trip.status == status)

        total = self.session.scalar(select(func.count(Trip.id)).where(*conditions)) or 0
        query = self._dashboard_query().where(*conditions).order_by(Trip.departs_at, Trip.id)
        rows = [DashboardRow(trip, count) for trip, count in self.session.execute(query.limit(limit).offset(offset))]
        return DashboardPage(rows, total, date_from, date_to, limit, offset)

    def dashboard_row(self, trip_id: int) -> DashboardRow:
        result = self.session.execute(self._dashboard_query().where(Trip.id == trip_id)).first()
        if result is None:
            raise errors.TripNotFound(f"Trip {trip_id} does not exist", trip_id=trip_id)
        return DashboardRow(*result)

    def change_status(self, trip_id: int, to_status: TripStatus) -> Trip:
        """Move a trip along the state machine in TRIP_TRANSITIONS."""
        with committing(self.session):
            trip = lock_trip(self.session, trip_id)
            allowed = TRIP_TRANSITIONS[trip.status]
            if to_status not in allowed:
                options = " or ".join(sorted(s.label.lower() for s in allowed)) or "nothing (it is final)"
                raise errors.InvalidTransition(
                    f"A {trip.status.label.lower()} trip can only move to {options}",
                    current=trip.status.value, requested=to_status.value,
                    allowed=sorted(s.value for s in allowed),
                )
            previous = trip.status
            trip.status = to_status
        self.events.publish(TripStatusChanged(trip_id, previous.value, to_status.value))
        return trip

    @staticmethod
    def _dashboard_query():
        bookings_count = select(func.count(Booking.id)).where(Booking.trip_id == Trip.id).scalar_subquery()
        return select(Trip, bookings_count).options(joinedload(Trip.origin), joinedload(Trip.destination))
