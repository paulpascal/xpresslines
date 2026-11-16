"""create towns trips bookings

Revision ID: 0001
Revises: 
Create Date: 2026-11-16 07:03:01.313116

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('towns',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=3), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('zone', sa.SmallInteger(), nullable=False),
    sa.CheckConstraint('zone BETWEEN 1 AND 4', name=op.f('ck_towns_zone_range')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_towns')),
    sa.UniqueConstraint('code', name=op.f('uq_towns_code')),
    sa.UniqueConstraint('name', name=op.f('uq_towns_name'))
    )
    op.create_table('trips',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('origin_id', sa.Integer(), nullable=False),
    sa.Column('destination_id', sa.Integer(), nullable=False),
    sa.Column('departs_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('capacity', sa.SmallInteger(), nullable=False),
    sa.Column('seats_booked', sa.SmallInteger(), nullable=False),
    sa.Column('status', sa.Enum('scheduled', 'boarding', 'departed', 'in_transit', 'arrived', 'completed', name='trip_status', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.CheckConstraint('capacity > 0', name=op.f('ck_trips_capacity_positive')),
    sa.CheckConstraint('origin_id <> destination_id', name=op.f('ck_trips_distinct_towns')),
    sa.CheckConstraint('seats_booked >= 0 AND seats_booked <= capacity', name=op.f('ck_trips_seats_within_capacity')),
    sa.ForeignKeyConstraint(['destination_id'], ['towns.id'], name=op.f('fk_trips_destination_id_towns')),
    sa.ForeignKeyConstraint(['origin_id'], ['towns.id'], name=op.f('fk_trips_origin_id_towns')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_trips'))
    )
    op.create_index('ix_trips_route_departure', 'trips', ['origin_id', 'destination_id', 'departs_at'], unique=False)
    op.create_table('bookings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=12), nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('passenger_name', sa.String(length=120), nullable=False),
    sa.Column('seats', sa.SmallInteger(), nullable=False),
    sa.Column('unit_fare', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('total_fare', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('idempotency_key', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('seats > 0', name=op.f('ck_bookings_seats_positive')),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], name=op.f('fk_bookings_trip_id_trips')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bookings')),
    sa.UniqueConstraint('idempotency_key', name=op.f('uq_bookings_idempotency_key')),
    sa.UniqueConstraint('reference', name=op.f('uq_bookings_reference'))
    )
    op.create_index(op.f('ix_bookings_trip_id'), 'bookings', ['trip_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_bookings_trip_id'), table_name='bookings')
    op.drop_table('bookings')
    op.drop_index('ix_trips_route_departure', table_name='trips')
    op.drop_table('trips')
    op.drop_table('towns')
