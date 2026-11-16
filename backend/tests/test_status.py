import pytest

from app.domain import errors
from app.domain.lifecycle import TripStatus

from .conftest import trip_service

LIFECYCLE = list(TripStatus)


def test_a_trip_walks_the_whole_lifecycle_one_step_at_a_time(session, make_trip):
    trip = make_trip()
    for status in LIFECYCLE[1:]:
        assert trip_service(session).change_status(trip.id, status).status == status


def test_skipping_a_step_is_refused(session, make_trip):
    trip = make_trip()
    with pytest.raises(errors.InvalidTransition) as refused:
        trip_service(session).change_status(trip.id, TripStatus.DEPARTED)
    assert refused.value.details["allowed"] == ["boarding"]


def test_going_back_is_refused(session, make_trip):
    trip = make_trip(status=TripStatus.DEPARTED)
    with pytest.raises(errors.InvalidTransition):
        trip_service(session).change_status(trip.id, TripStatus.BOARDING)


def test_completed_is_final(session, make_trip):
    trip = make_trip(status=TripStatus.COMPLETED)
    with pytest.raises(errors.InvalidTransition, match="final"):
        trip_service(session).change_status(trip.id, TripStatus.COMPLETED)


def test_next_status_follows_the_spec_order():
    assert [s.label for s in LIFECYCLE] == [
        "Scheduled", "Boarding", "Departed", "In transit", "Arrived", "Completed",
    ]
    assert TripStatus.ARRIVED.next == TripStatus.COMPLETED
    assert TripStatus.COMPLETED.next is None


def test_every_status_is_in_the_state_machine_and_follows_the_spec():
    from app.domain.lifecycle import TRIP_TRANSITIONS

    assert set(TRIP_TRANSITIONS) == set(TripStatus)
    for status in LIFECYCLE[:-1]:
        assert TRIP_TRANSITIONS[status] == {status.next}
    assert TRIP_TRANSITIONS[TripStatus.COMPLETED] == set()
