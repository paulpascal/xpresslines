"""Operational checks, meant to run on a schedule and feed an alert."""

import click
from flask import current_app
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.models import Booking, Trip


def seat_counter_drift(session: Session) -> list[tuple[int, int, int]]:
    """Trips whose seats_booked differs from the sum of their bookings: (trip_id, counter, actual)."""
    actual = func.coalesce(func.sum(Booking.seats), 0)
    query = (
        select(Trip.id, Trip.seats_booked, actual)
        .outerjoin(Booking, Booking.trip_id == Trip.id)
        .group_by(Trip.id)
        .having(Trip.seats_booked != actual)
    )
    return [tuple(row) for row in session.execute(query)]


@click.command("check-seats")
def check_seats_command() -> None:
    """Exit with an error if any trip's seat counter has drifted."""
    with current_app.extensions["session_factory"]() as session:
        drift = seat_counter_drift(session)
    for trip_id, counter, actual in drift:
        click.echo(f"trip {trip_id}: seats_booked={counter} but bookings add up to {actual}")
    if drift:
        raise SystemExit(1)
    click.echo("OK: every seat counter matches its bookings.")
