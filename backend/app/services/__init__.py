"""Use cases, as classes whose dependencies are passed in, never imported globals.

`Services` holds the dependencies chosen once at startup (in create_app) and
builds a service per request around that request's database session.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..domain.booking_rules import BookingRule
from ..domain.clock import Clock
from ..domain.events import EventBus
from ..domain.pricing import FarePolicy
from .booking import BookingService
from .trips import TripService


@dataclass(frozen=True)
class Services:
    pricing: FarePolicy
    booking_rules: Sequence[BookingRule]
    clock: Clock
    events: EventBus

    def booking(self, session: Session) -> BookingService:
        return BookingService(session, self.pricing, self.booking_rules, self.clock, self.events)

    def trips(self, session: Session) -> TripService:
        return TripService(session, self.pricing, self.clock, self.events)


__all__ = ["BookingService", "Services", "TripService"]
