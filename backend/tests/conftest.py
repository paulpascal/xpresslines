"""Tests run against a real PostgreSQL database (bus_test), migrated with
Alembic, because the booking guarantees depend on real row locks."""

import os
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.cli.seed import TOWNS
from app.domain.booking_rules import DEFAULT_BOOKING_RULES
from app.domain.events import EventBus
from app.domain.lifecycle import TripStatus
from app.domain.models import Town, Trip
from app.domain.pricing import ZoneFareTable
from app.infra.db import make_session_factory
from app.services import BookingService, Services, TripService

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://bus:bus@localhost:55432/bus_test"
)
NOW = datetime.now(UTC).replace(microsecond=0)


def make_services(**overrides) -> Services:
    """Real policies and rules, a fixed clock, a fresh event bus. Override any of them."""
    return Services(**{
        "pricing": ZoneFareTable(),
        "booking_rules": DEFAULT_BOOKING_RULES,
        "clock": lambda: NOW,
        "events": EventBus(),
        **overrides,
    })


def booking_service(session, **overrides) -> BookingService:
    return make_services(**overrides).booking(session)


def trip_service(session, **overrides) -> TripService:
    return make_services(**overrides).trips(session)


def _create_database_if_missing(url: str) -> None:
    url = make_url(url)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def session_factory():
    _create_database_if_missing(TEST_DATABASE_URL)
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "migrations"))
    alembic_cfg.attributes["database_url"] = TEST_DATABASE_URL
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
    return make_session_factory(TEST_DATABASE_URL)


@pytest.fixture
def session(session_factory):
    with session_factory() as s:
        s.execute(text("TRUNCATE bookings, trips, towns RESTART IDENTITY CASCADE"))
        s.commit()
        yield s


@pytest.fixture
def towns(session):
    created = {code: Town(code=code, name=name, zone=zone) for code, name, zone in TOWNS}
    session.add_all(created.values())
    session.commit()
    return created


@pytest.fixture
def make_trip(session, towns):
    def _make(origin="LOS", destination="ABV", capacity=44, seats_booked=0,
              status=TripStatus.SCHEDULED, departs_at=NOW + timedelta(days=1)):
        trip = Trip(origin=towns[origin], destination=towns[destination], capacity=capacity,
                    seats_booked=seats_booked, status=status, departs_at=departs_at)
        session.add(trip)
        session.commit()
        return trip
    return _make


@pytest.fixture
def client(session):
    from app import create_app  # imported here: service tests never need the HTTP layer

    app = create_app(TEST_DATABASE_URL)
    app.config["TESTING"] = True
    return app.test_client()
