"""Fare rules. No database or framework, so they are trivial to test and to replace."""

from decimal import Decimal
from typing import Protocol

CURRENCY = "USD"

# Base fare per journey between two zones, from the operator's fare table.
# Keyed by (lower zone, higher zone) because fares are the same both ways.
ZONE_FARES: dict[tuple[int, int], Decimal] = {
    (1, 1): Decimal("8.00"),
    (1, 2): Decimal("18.00"),
    (1, 3): Decimal("25.00"),
    (1, 4): Decimal("35.00"),
    (2, 2): Decimal("10.00"),
    (2, 3): Decimal("18.00"),
    (2, 4): Decimal("28.00"),
    (3, 3): Decimal("8.00"),
    (3, 4): Decimal("22.00"),
    (4, 4): Decimal("8.00"),
}


class UnknownFare(LookupError):
    pass


class FarePolicy(Protocol):
    """How the unit fare is decided (Strategy pattern).

    Services receive a policy at construction; a new way of pricing (fares
    stored in the database, peak-season surcharge, a second operator with its
    own prices) is a new class chosen in create_app, with no change to the
    booking or search code.
    """

    def fare(self, zone_a: int, zone_b: int) -> Decimal: ...


class ZoneFareTable:
    """The operator's fixed zone table: O(1) lookup, same fare both ways."""

    def __init__(self, fares: dict[tuple[int, int], Decimal] = ZONE_FARES):
        self._fares = fares

    def fare(self, zone_a: int, zone_b: int) -> Decimal:
        key = (min(zone_a, zone_b), max(zone_a, zone_b))
        try:
            return self._fares[key]
        except KeyError:
            raise UnknownFare(f"No fare defined between zone {zone_a} and zone {zone_b}") from None


def total_fare(unit_fare: Decimal, seats: int) -> Decimal:
    return unit_fare * seats
