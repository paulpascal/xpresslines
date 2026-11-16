"""The HTTP contract, end to end through Flask."""

import time
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.domain.lifecycle import TripStatus


def tomorrow():
    return datetime.now(UTC) + timedelta(days=1)


def test_price_search_and_book_a_seat(client, make_trip):
    trip = make_trip("LOS", "KAN", departs_at=tomorrow())

    fare = client.get("/api/v1/fares?origin=LOS&destination=KAN").get_json()
    assert fare["fare"] == {"amount": "35.00", "currency": "USD"}

    search = client.get("/api/v1/trips?origin=los&destination=kan").get_json()
    assert [t["id"] for t in search["trips"]] == [trip.id]
    assert search["trips"][0]["departs_at"].endswith("+01:00")  # Lagos time

    response = client.post("/api/v1/bookings", json={
        "trip_id": trip.id, "passenger_name": "Ada Obi", "seats": 2,
    })
    assert response.status_code == 201
    booking = response.get_json()
    assert booking["passenger_name"] == "ADA OBI"
    assert booking["total_fare"] == {"amount": "70.00", "currency": "USD"}

    fetched = client.get(f"/api/v1/bookings/{booking['reference']}").get_json()
    assert fetched["trip"]["seats_available"] == 42


def test_retry_with_idempotency_key_returns_200_and_same_booking(client, make_trip):
    trip = make_trip(departs_at=tomorrow())
    body = {"trip_id": trip.id, "passenger_name": "Ada Obi", "seats": 1}
    headers = {"Idempotency-Key": "abc-123"}

    first = client.post("/api/v1/bookings", json=body, headers=headers)
    retry = client.post("/api/v1/bookings", json=body, headers=headers)

    assert (first.status_code, retry.status_code) == (201, 200)
    assert first.get_json()["reference"] == retry.get_json()["reference"]


def test_validation_errors_name_the_fields(client, towns):
    response = client.post("/api/v1/bookings", json={"trip_id": 1, "passenger_name": "", "seats": "two"})
    assert response.status_code == 422
    fields = {f["field"] for f in response.get_json()["error"]["details"]["fields"]}
    assert fields == {"passenger_name", "seats"}


def test_not_enough_seats_is_a_409_with_seats_left(client, make_trip):
    trip = make_trip(capacity=14, seats_booked=13, departs_at=tomorrow())
    response = client.post("/api/v1/bookings", json={"trip_id": trip.id, "passenger_name": "Ada", "seats": 2})
    assert response.status_code == 409
    error = response.get_json()["error"]
    assert error["code"] == "not_enough_seats"
    assert error["details"]["seats_available"] == 1


def test_unknown_town_is_404_and_same_town_is_422(client, towns):
    assert client.get("/api/v1/trips?origin=LOS&destination=XYZ").status_code == 404
    assert client.get("/api/v1/trips?origin=LOS&destination=LOS").status_code == 422


def test_dashboard_lists_every_trip_with_bookings_so_far(client, make_trip):
    trip = make_trip(capacity=44, departs_at=tomorrow())
    make_trip(status=TripStatus.ARRIVED, departs_at=tomorrow() - timedelta(days=3))
    client.post("/api/v1/bookings", json={"trip_id": trip.id, "passenger_name": "Ada", "seats": 3})

    rows = client.get("/api/v1/admin/trips").get_json()["trips"]
    assert len(rows) == 2
    row = next(r for r in rows if r["id"] == trip.id)
    assert (row["capacity"], row["seats_booked"], row["bookings_count"], row["status"]) == (44, 3, 1, "scheduled")

    arrived = client.get("/api/v1/admin/trips?status=arrived").get_json()["trips"]
    assert [r["status"] for r in arrived] == ["arrived"]


def test_operator_moves_a_trip_forward(client, make_trip):
    trip = make_trip(departs_at=tomorrow())
    ok = client.post(f"/api/v1/admin/trips/{trip.id}/status", json={"status": "boarding"})
    assert ok.status_code == 200 and ok.get_json()["next_status"] == "departed"

    skip = client.post(f"/api/v1/admin/trips/{trip.id}/status", json={"status": "arrived"})
    assert skip.status_code == 409


def test_health_and_unknown_routes(client, towns):
    assert client.get("/api/v1/health").get_json() == {"status": "ok"}
    assert client.get("/api/v1/nope").status_code == 404


def test_hostile_input_gets_a_4xx_never_a_500(client, make_trip):
    trip = make_trip(departs_at=tomorrow())
    body = {"trip_id": trip.id, "passenger_name": "Ada", "seats": 1}

    long_key = client.post("/api/v1/bookings", json=body, headers={"Idempotency-Key": "k" * 65})
    nul_name = client.post("/api/v1/bookings", json={**body, "passenger_name": "Ab\u0000c"})
    huge_trip = client.post("/api/v1/bookings", json={**body, "trip_id": 2**40})
    boolean_seats = client.post("/api/v1/bookings", json={**body, "seats": True})
    not_json = client.post("/api/v1/bookings", data="seats=1", content_type="text/plain")

    assert [r.status_code for r in (long_key, nul_name, boolean_seats, not_json)] == [422] * 4
    grows_when_capitalised = client.post("/api/v1/bookings", json={**body, "passenger_name": "ß" * 61})
    assert grows_when_capitalised.status_code == 422
    assert huge_trip.status_code == 404
    assert client.get("/api/v1/bookings/%00abcdef").status_code == 422
    assert client.get("/api/v1/fares?origin=L%00S&destination=ABV").status_code == 422
    assert client.post("/api/v1/admin/trips/99999999999/status", json={"status": "boarding"}).status_code == 404


def test_a_stuck_lock_fails_fast_with_503_instead_of_hanging(client, make_trip, session_factory):
    # Someone holds the trip row (a hung transaction, a forgotten psql session).
    trip = make_trip(departs_at=tomorrow())
    blocker = session_factory()
    blocker.execute(text("SELECT id FROM trips WHERE id = :id FOR UPDATE"), {"id": trip.id})
    try:
        started = time.monotonic()
        response = client.post("/api/v1/bookings", json={"trip_id": trip.id, "passenger_name": "Ada", "seats": 1})
        waited = time.monotonic() - started
    finally:
        blocker.rollback()
        blocker.close()

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "service_busy"
    assert waited < 4  # lock_timeout, not forever


def test_health_says_503_when_the_database_is_down():
    from app import create_app

    app = create_app("postgresql+psycopg://bus:bus@localhost:1/nowhere")
    assert app.test_client().get("/api/v1/health").status_code == 503


def test_dashboard_shows_all_trips_one_page_at_a_time(client, make_trip):
    soon = make_trip(departs_at=tomorrow())
    later = make_trip(departs_at=tomorrow() + timedelta(days=1))
    far = make_trip(departs_at=tomorrow() + timedelta(days=30))

    everything = client.get("/api/v1/admin/trips").get_json()
    assert [t["id"] for t in everything["trips"]] == [soon.id, later.id, far.id]

    page_two = client.get("/api/v1/admin/trips?limit=1&offset=1").get_json()
    assert (page_two["total"], [t["id"] for t in page_two["trips"]]) == (3, [later.id])

    this_week = client.get(f"/api/v1/admin/trips?date_to={(tomorrow() + timedelta(days=7)).date()}").get_json()
    assert [t["id"] for t in this_week["trips"]] == [soon.id, later.id]

    assert client.get("/api/v1/admin/trips?date_from=2026-12-10&date_to=2026-12-01").status_code == 422
    assert client.get("/api/v1/admin/trips?limit=500").status_code == 422


def test_app_refuses_to_start_with_more_threads_than_connections(monkeypatch):
    from app import config, create_app

    monkeypatch.setattr(config, "THREADS", 20)
    with pytest.raises(RuntimeError, match="THREADS=20"):
        create_app()
