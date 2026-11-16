"""Database-level defaults, so rows inserted outside the app are still valid

Additive and safe on a live database: only column defaults change, no data
is rewritten and no lock is held beyond a quick catalog update.

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("trips", "seats_booked", server_default="0")
    op.alter_column("trips", "status", server_default="scheduled")
    op.alter_column("bookings", "currency", server_default="USD")


def downgrade() -> None:
    op.alter_column("bookings", "currency", server_default=None)
    op.alter_column("trips", "status", server_default=None)
    op.alter_column("trips", "seats_booked", server_default=None)
