from decimal import Decimal
from itertools import product

import pytest

from app.domain.pricing import ZONE_FARES, UnknownFare, ZoneFareTable, total_fare

fare_between_zones = ZoneFareTable().fare

SPEC_FARES = [
    (1, 1, "8"), (1, 2, "18"), (1, 3, "25"), (1, 4, "35"),
    (2, 2, "10"), (2, 3, "18"), (2, 4, "28"),
    (3, 3, "8"), (3, 4, "22"),
    (4, 4, "8"),
]


@pytest.mark.parametrize("from_zone,to_zone,fare", SPEC_FARES)
def test_every_fare_in_the_spec(from_zone, to_zone, fare):
    assert fare_between_zones(from_zone, to_zone) == Decimal(fare)


@pytest.mark.parametrize("zone_a,zone_b", product(range(1, 5), repeat=2))
def test_fares_are_the_same_in_both_directions(zone_a, zone_b):
    assert fare_between_zones(zone_a, zone_b) == fare_between_zones(zone_b, zone_a)


def test_all_sixteen_zone_pairs_have_a_fare():
    for zone_a, zone_b in product(range(1, 5), repeat=2):
        fare_between_zones(zone_a, zone_b)  # does not raise
    assert len(ZONE_FARES) == 10


def test_unknown_zone_is_an_error_not_a_free_ride():
    with pytest.raises(UnknownFare):
        fare_between_zones(1, 5)


def test_total_is_unit_fare_times_seats_without_float_rounding():
    assert total_fare(Decimal("18.00"), 3) == Decimal("54.00")
    assert isinstance(total_fare(Decimal("18.00"), 3), Decimal)
