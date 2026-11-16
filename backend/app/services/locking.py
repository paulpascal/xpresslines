"""The one way to lock a trip row, shared by every write on a trip."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain import errors
from ..domain.models import Trip

MAX_DB_ID = 2**31 - 1  # Postgres INTEGER


def lock_trip(session: Session, trip_id: int) -> Trip:
    """SELECT ... FOR UPDATE on the trip: concurrent writers on this bus queue here."""
    if not 0 < trip_id <= MAX_DB_ID:  # would be a database error, not a 404
        raise errors.TripNotFound(f"Trip {trip_id} does not exist", trip_id=trip_id)
    trip = session.scalar(
        select(Trip)
        .where(Trip.id == trip_id)
        .with_for_update(of=Trip)
        # Refresh from the row we just locked, never trust a stale copy
        # already sitting in the session's identity map.
        .execution_options(populate_existing=True)
    )
    if trip is None:
        raise errors.TripNotFound(f"Trip {trip_id} does not exist", trip_id=trip_id)
    return trip
