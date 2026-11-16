"""Domain events (observer pattern): services announce what happened, after commit.

Side effects (SMS confirmation, analytics, a job queue) subscribe to an event
instead of being written into the booking code. They run after the commit, so
they never hold the seat lock, and a failing subscriber never undoes a booking.
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from decimal import Decimal

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BookingCreated:
    reference: str
    trip_id: int
    seats: int
    total_fare: Decimal
    seats_left: int


@dataclass(frozen=True)
class BookingRejected:
    trip_id: int
    reason: str
    details: dict


@dataclass(frozen=True)
class TripStatusChanged:
    trip_id: int
    previous: str
    current: str


Event = BookingCreated | BookingRejected | TripStatusChanged
ALL_EVENTS: tuple[type, ...] = (BookingCreated, BookingRejected, TripStatusChanged)
Handler = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers[type(event)]:
            try:
                handler(event)
            except Exception:
                log.exception("event_handler_failed", extra={"fields": {
                    "event_type": type(event).__name__, "handler": getattr(handler, "__name__", repr(handler)),
                }})


def log_event(event: Event) -> None:
    """Default subscriber: every event becomes a structured log line."""
    fields = {k: str(v) if isinstance(v, Decimal) else v for k, v in asdict(event).items()}
    log.info(type(event).__name__, extra={"fields": fields})
