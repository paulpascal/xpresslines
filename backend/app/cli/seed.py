"""Demo data: 6 towns, 10 trips, 17 bookings.

Trip times are relative to "now" (Lagos time), so a fresh seed always has
upcoming trips to book, a trip boarding, one on the road and one arrived.
Run: flask --app app seed            (only if the database is empty)
     flask --app app seed --reset    (wipe and reseed)
"""

from datetime import datetime, timedelta

import click
from flask import current_app
from sqlalchemy import func, select, text

from ..config import OPERATOR_TZ
from ..domain.booking import new_reference, normalize_passenger_name
from ..domain.lifecycle import TripStatus
from ..domain.models import Booking, Town, Trip
from ..domain.pricing import CURRENCY, FarePolicy, total_fare

TOWNS = [
    # code, name, zone
    ("LOS", "Lagos", 1),
    ("IBA", "Ibadan", 1),
    ("ENU", "Enugu", 2),
    ("ONI", "Onitsha", 2),
    ("ABV", "Abuja", 3),
    ("KAN", "Kano", 4),
]

# origin, destination, when, capacity, status, bookings [(name, seats)]
# "when" is either hours from now, or (days from today, "HH:MM") in Lagos time.
# Fleet: 7-seat shared car (Toyota Sienna), 15-seat minibus (Toyota Hiace),
# 30-seat midibus (Toyota Coaster), 50-seat coach. Most customers book 1 or 2
# seats, a family 3. Upcoming trips are still selling; trips on the road are full.
TRIPS = [
    ("LOS", "ABV", 4, 15, TripStatus.SCHEDULED,
     [("Adebayo Ogunleye", 2), ("Chiamaka Okafor", 1)]),
    ("LOS", "ABV", (1, "06:30"), 50, TripStatus.SCHEDULED, [("Musa Abdullahi", 3)]),
    # One seat left: the last-seat demo.
    ("LOS", "ABV", (1, "14:00"), 7, TripStatus.SCHEDULED,
     [("Emeka Nwosu", 2), ("Aisha Bello", 1), ("Tunde Bakare", 3)]),
    ("LOS", "IBA", (1, "08:00"), 15, TripStatus.SCHEDULED, [("Ngozi Eze", 2)]),
    ("ABV", "KAN", (1, "07:00"), 30, TripStatus.SCHEDULED, [("Halima Sani", 1)]),
    ("ENU", "LOS", (2, "05:30"), 50, TripStatus.SCHEDULED, []),
    ("ONI", "ABV", (2, "09:00"), 30, TripStatus.SCHEDULED, []),
    ("IBA", "ENU", 0.5, 7, TripStatus.BOARDING,
     [("Yetunde Alabi", 2), ("Grace Etim", 3), ("Ibrahim Yusuf", 1)]),
    ("LOS", "KAN", -2, 7, TripStatus.DEPARTED,
     [("Sadiq Lawal", 2), ("Blessing Okon", 3), ("Segun Afolabi", 2)]),
    ("KAN", "ABV", (-1, "07:00"), 7, TripStatus.ARRIVED,
     [("Zainab Garba", 3), ("Amaka Obi", 2), ("Bello Garba", 2)]),
]


def departure_time(when, now: datetime) -> datetime:
    if isinstance(when, tuple):
        days, hh_mm = when
        hour, minute = map(int, hh_mm.split(":"))
        day = now.date() + timedelta(days=days)
        return datetime(day.year, day.month, day.day, hour, minute, tzinfo=OPERATOR_TZ)
    return (now + timedelta(hours=when)).replace(second=0, microsecond=0)


def seed(session, pricing: FarePolicy, now: datetime | None = None) -> None:
    now = now or datetime.now(OPERATOR_TZ)
    towns = {code: Town(code=code, name=name, zone=zone) for code, name, zone in TOWNS}
    session.add_all(towns.values())

    for origin, destination, when, capacity, status, bookings in TRIPS:
        trip = Trip(
            origin=towns[origin],
            destination=towns[destination],
            departs_at=departure_time(when, now),
            capacity=capacity,
            status=status,
            seats_booked=sum(seats for _, seats in bookings),
        )
        unit_fare = pricing.fare(towns[origin].zone, towns[destination].zone)
        for passenger_name, seats in bookings:
            session.add(Booking(
                reference=new_reference(),
                trip=trip,
                passenger_name=normalize_passenger_name(passenger_name),
                seats=seats,
                unit_fare=unit_fare,
                total_fare=total_fare(unit_fare, seats),
                currency=CURRENCY,
            ))
        session.add(trip)
    session.commit()


def wipe(session) -> None:
    session.execute(text("TRUNCATE bookings, trips, towns RESTART IDENTITY CASCADE"))
    session.commit()


@click.command("seed")
@click.option("--reset", is_flag=True, help="Delete all data first, then seed.")
def seed_command(reset: bool) -> None:
    """Load the demo towns, trips and bookings."""
    with current_app.extensions["session_factory"]() as session:
        if reset:
            wipe(session)
        elif session.scalar(select(func.count(Town.id))):
            click.echo("Database already has data, nothing to do (use --reset to reseed).")
            return
        seed(session, current_app.extensions["services"].pricing)
        trips = session.scalar(select(func.count(Trip.id)))
        bookings = session.scalar(select(func.count(Booking.id)))
        click.echo(f"Seeded {len(TOWNS)} towns, {trips} trips, {bookings} bookings.")
