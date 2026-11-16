"""The trip lifecycle, as an explicit state machine."""

import enum


class TripStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    COMPLETED = "completed"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").capitalize()

    @property
    def next(self) -> "TripStatus | None":
        """The normal next step, shown to operators as their next action."""
        members = list(TripStatus)
        position = members.index(self)
        return members[position + 1] if position + 1 < len(members) else None


# Every allowed move is listed. Adding a state (e.g. CANCELLED from SCHEDULED
# or BOARDING) is a line here, not an if-else hunt through the code.
TRIP_TRANSITIONS: dict[TripStatus, frozenset[TripStatus]] = {
    TripStatus.SCHEDULED: frozenset({TripStatus.BOARDING}),
    TripStatus.BOARDING: frozenset({TripStatus.DEPARTED}),
    TripStatus.DEPARTED: frozenset({TripStatus.IN_TRANSIT}),
    TripStatus.IN_TRANSIT: frozenset({TripStatus.ARRIVED}),
    TripStatus.ARRIVED: frozenset({TripStatus.COMPLETED}),
    TripStatus.COMPLETED: frozenset(),
}
