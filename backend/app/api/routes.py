"""HTTP routes: declare inputs and outputs, call a service, serialise.

Each route's typed parameters (query, body, header, path) are validated by
flask-openapi3, and the same declarations generate the API docs at
/api/v1/docs/swagger. A route's docstring is its documentation: first line
is the summary, the rest the description. No business rules live here.
"""

from typing import Any

from flask import current_app, g, jsonify
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel
from sqlalchemy import text

from ..services import BookingService, Services, TripService
from .schemas import (
    BookingHeaders,
    BookingOut,
    BookingPath,
    BookingRequest,
    DashboardOut,
    DashboardQuery,
    DashboardTripOut,
    ErrorOut,
    FareOut,
    FareQuery,
    HealthOut,
    SearchOut,
    SearchQuery,
    StatusChangeRequest,
    TownOut,
    TownsOut,
    TripOut,
    TripPath,
)

bp = APIBlueprint("api", __name__, url_prefix="/api/v1")

CUSTOMER = Tag(name="Customer", description="Search, price and book")
OPERATOR = Tag(name="Operator", description="Trusted operator endpoints (no auth in this prototype)")
SYSTEM = Tag(name="System")

Responses = dict[str | int, Any]
NOT_FOUND: Responses = {404: ErrorOut}
REFUSED: Responses = {409: ErrorOut}


def booking_service() -> BookingService:
    services: Services = current_app.extensions["services"]
    return services.booking(g.db)


def trip_service() -> TripService:
    services: Services = current_app.extensions["services"]
    return services.trips(g.db)


def ok(payload: BaseModel | list[BaseModel], status: int = 200):
    body: Any
    if isinstance(payload, list):
        body = [item.model_dump(mode="json") for item in payload]
    else:
        body = payload.model_dump(mode="json")
    return jsonify(body), status


@bp.get("/health", tags=[SYSTEM], responses={200: HealthOut})
def health():
    """Liveness and database check"""
    g.db.execute(text("SELECT 1"))
    return jsonify(status="ok")


# Customer endpoints

@bp.get("/towns", tags=[CUSTOMER], responses={200: TownsOut})
def list_towns():
    """List the 6 towns with their pricing zone"""
    return ok([TownOut.of(town) for town in trip_service().towns()])


@bp.get("/fares", tags=[CUSTOMER], responses={200: FareOut, **NOT_FOUND})
def get_fare(query: FareQuery):
    """Price one adult seat between two towns

    Fares depend only on the two zones and are the same in both directions.
    """
    return ok(FareOut.of(trip_service().quote(query.origin, query.destination)))


@bp.get("/trips", tags=[CUSTOMER], responses={200: SearchOut, **NOT_FOUND})
def search_trips(query: SearchQuery):
    """Search bookable trips on a route

    Scheduled trips that have not left yet, soonest first, with the fare and seats
    left. `date` is a Lagos calendar day; omit it for every upcoming trip. Sold-out
    trips are included with `seats_available: 0`.
    """
    quote, trips = trip_service().search(query.origin, query.destination, query.date)
    return ok(SearchOut(
        **FareOut.of(quote).model_dump(),
        date=query.date,
        trips=[TripOut.of(trip) for trip in trips],
    ))


@bp.post("/bookings", tags=[CUSTOMER], responses={201: BookingOut, 200: BookingOut, **NOT_FOUND, **REFUSED})
def create_booking(body: BookingRequest, header: BookingHeaders):
    """Book seats on a trip

    Safe under concurrency: the trip row is locked during the check-and-book, so a
    bus is never oversold (409 when seats run out). Safe to retry: with the same
    `Idempotency-Key`, you get the original booking back (200) instead of a second one (201).
    """
    result = booking_service().book(
        trip_id=body.trip_id,
        passenger_name=body.passenger_name,
        seats=body.seats,
        idempotency_key=header.idempotency_key or None,
    )
    return ok(BookingOut.of(result.booking), 201 if result.created else 200)


@bp.get("/bookings/<reference>", tags=[CUSTOMER], responses={200: BookingOut, **NOT_FOUND})
def get_booking(path: BookingPath):
    """Look up a booking by its reference"""
    return ok(BookingOut.of(booking_service().get(path.reference)))


# Operator endpoints

@bp.get("/admin/trips", tags=[OPERATOR], responses={200: DashboardOut})
def dashboard_trips(query: DashboardQuery):
    """Dashboard: all trips with capacity, bookings so far and status

    Soonest first, paginated with `limit` (max 100) and `offset`. Optional filters:
    `status`, and `date_from` / `date_to` (Lagos days).
    """
    page = trip_service().dashboard(
        status=query.status, date_from=query.date_from, date_to=query.date_to,
        limit=query.limit, offset=query.offset,
    )
    return ok(DashboardOut.of(page))


@bp.post("/admin/trips/<int:trip_id>/status", tags=[OPERATOR],
         responses={200: DashboardTripOut, **NOT_FOUND, **REFUSED})
def change_trip_status(path: TripPath, body: StatusChangeRequest):
    """Move a trip to its next status

    Scheduled, Boarding, Departed, In transit, Arrived, Completed: one step forward
    at a time, no skipping, no going back (409 otherwise).
    """
    trips = trip_service()
    trips.change_status(path.trip_id, body.status)
    return ok(DashboardTripOut.of_row(trips.dashboard_row(path.trip_id)))
