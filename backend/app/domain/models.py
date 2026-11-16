"""Database tables and the invariants the database itself enforces."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    MetaData,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .lifecycle import TripStatus

# Stable constraint names, so Alembic migrations stay readable and diffable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Town(Base):
    __tablename__ = "towns"
    __table_args__ = (CheckConstraint("zone BETWEEN 1 AND 4", name="zone_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(3), unique=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    zone: Mapped[int] = mapped_column(SmallInteger)


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="capacity_positive"),
        # The last line of defence against overbooking: even a buggy code path
        # or a manual SQL update cannot push a bus past its capacity.
        CheckConstraint(
            "seats_booked >= 0 AND seats_booked <= capacity", name="seats_within_capacity"
        ),
        CheckConstraint("origin_id <> destination_id", name="distinct_towns"),
        Index("ix_trips_route_departure", "origin_id", "destination_id", "departs_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    origin_id: Mapped[int] = mapped_column(ForeignKey("towns.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("towns.id"))
    departs_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(SmallInteger)
    # Denormalised running total of Booking.seats, only ever changed by
    # BookingService.book while the trip row is locked.
    seats_booked: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    status: Mapped[TripStatus] = mapped_column(
        Enum(
            TripStatus,
            name="trip_status",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda statuses: [s.value for s in statuses],
        ),
        default=TripStatus.SCHEDULED,
        server_default=TripStatus.SCHEDULED.value,
    )

    origin: Mapped[Town] = relationship(foreign_keys=[origin_id])
    destination: Mapped[Town] = relationship(foreign_keys=[destination_id])
    bookings: Mapped[list["Booking"]] = relationship(back_populates="trip")

    @property
    def seats_available(self) -> int:
        return self.capacity - self.seats_booked


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (CheckConstraint("seats > 0", name="seats_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(12), unique=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    passenger_name: Mapped[str] = mapped_column(String(120))
    seats: Mapped[int] = mapped_column(SmallInteger)
    # Price snapshot at booking time: a later fare change never rewrites history.
    unit_fare: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    total_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")
    # Optional client-supplied key so a retried request never books twice.
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    trip: Mapped[Trip] = relationship(back_populates="bookings")
