"""API contract: what comes in (validated) and what goes out (serialised)."""

import datetime as dt
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel, StringConstraints

from ..config import OPERATOR_TZ
from ..domain.lifecycle import TripStatus
from ..domain.models import Booking, Town, Trip
from ..services.trips import DashboardPage, DashboardRow, Quote

TownCode = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{3}$")]


# Requests

class SearchQuery(BaseModel):
    origin: TownCode
    destination: TownCode
    date: dt.date | None = None


class FareQuery(BaseModel):
    origin: TownCode
    destination: TownCode


class BookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_id: int = Field(gt=0, strict=True)
    # No control characters (Postgres rejects NUL bytes, and they have no place in a name).
    passenger_name: Annotated[str, StringConstraints(
        strip_whitespace=True, min_length=2, max_length=120, pattern=r"^[^\x00-\x1f\x7f]+$",
    )]
    seats: int = Field(ge=1, strict=True)


class BookingHeaders(BaseModel):
    idempotency_key: str | None = Field(
        None, alias="Idempotency-Key", max_length=64,
        description="Unique per booking intent (e.g. a UUID). A retry with the same key returns "
                    "the original booking instead of booking twice.",
    )


class TripPath(BaseModel):
    trip_id: int


class BookingPath(BaseModel):
    reference: str = Field(pattern=r"^[A-Za-z0-9]{8}$")


class StatusChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TripStatus


class DashboardQuery(BaseModel):
    status: TripStatus | None = None
    date_from: dt.date | None = Field(None, description="Only trips departing on or after this Lagos day")
    date_to: dt.date | None = Field(None, description="Only trips departing on or before this Lagos day")
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


# Responses

class Money(BaseModel):
    amount: Decimal
    currency: str


class TownOut(BaseModel):
    code: str
    name: str
    zone: int

    @classmethod
    def of(cls, town: Town) -> "TownOut":
        return cls(code=town.code, name=town.name, zone=town.zone)


def local_time(value: dt.datetime) -> dt.datetime:
    return value.astimezone(OPERATOR_TZ)


class FareOut(BaseModel):
    origin: TownOut
    destination: TownOut
    fare: Money

    @classmethod
    def of(cls, quote: Quote) -> "FareOut":
        return cls(
            origin=TownOut.of(quote.origin),
            destination=TownOut.of(quote.destination),
            fare=Money(amount=quote.unit_fare, currency=quote.currency),
        )


class TripOut(BaseModel):
    id: int
    origin: TownOut
    destination: TownOut
    departs_at: dt.datetime
    capacity: int
    seats_available: int
    status: TripStatus

    @classmethod
    def of(cls, trip: Trip) -> "TripOut":
        return cls(
            id=trip.id,
            origin=TownOut.of(trip.origin),
            destination=TownOut.of(trip.destination),
            departs_at=local_time(trip.departs_at),
            capacity=trip.capacity,
            seats_available=trip.seats_available,
            status=trip.status,
        )


class SearchOut(FareOut):
    date: dt.date | None
    trips: list[TripOut]


class BookingOut(BaseModel):
    reference: str
    passenger_name: str
    seats: int
    unit_fare: Money
    total_fare: Money
    created_at: dt.datetime
    trip: TripOut

    @classmethod
    def of(cls, booking: Booking) -> "BookingOut":
        return cls(
            reference=booking.reference,
            passenger_name=booking.passenger_name,
            seats=booking.seats,
            unit_fare=Money(amount=booking.unit_fare, currency=booking.currency),
            total_fare=Money(amount=booking.total_fare, currency=booking.currency),
            created_at=local_time(booking.created_at),
            trip=TripOut.of(booking.trip),
        )


class DashboardTripOut(TripOut):
    seats_booked: int
    bookings_count: int
    next_status: TripStatus | None

    @classmethod
    def of_row(cls, row: DashboardRow) -> "DashboardTripOut":
        return cls(
            **TripOut.of(row.trip).model_dump(),
            seats_booked=row.trip.seats_booked,
            bookings_count=row.bookings_count,
            next_status=row.trip.status.next,
        )


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict


class ErrorOut(BaseModel):
    error: ErrorBody


class TownsOut(RootModel[list[TownOut]]):
    pass


class DashboardOut(BaseModel):
    date_from: dt.date | None
    date_to: dt.date | None
    total: int
    limit: int
    offset: int
    trips: list[DashboardTripOut]

    @classmethod
    def of(cls, page: DashboardPage) -> "DashboardOut":
        return cls(
            date_from=page.date_from, date_to=page.date_to, total=page.total,
            limit=page.limit, offset=page.offset,
            trips=[DashboardTripOut.of_row(row) for row in page.rows],
        )


class HealthOut(BaseModel):
    status: str
