"""add received_at to events

Revision ID: 7f403321615c
Revises: 36cd7d09ae69
Create Date: 2026-09-02 23:14:27.849777

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f403321615c"
down_revision: str | Sequence[str] | None = "36cd7d09ae69"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the column as nullable first because existing rows do not have a
    # received_at value yet. This allows us to migrate existing data safely
    # before enforcing the NOT NULL constraint.
    op.add_column(
        "events",
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Backfill existing events with the migration timestamp. Their real
    # historical reception time is unknown, so CURRENT_TIMESTAMP provides a
    # consistent value before enforcing the NOT NULL constraint.
    op.execute(
        sa.text(
            """
            UPDATE events
            SET received_at = CURRENT_TIMESTAMP
            WHERE received_at IS NULL
            """
        )
    )

    # Use Alembic batch operations so the schema change remains portable
    # across database engines. Alembic can recreate the table when required
    # by the backend and use native ALTER TABLE operations where supported.
    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "received_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Use the same portable batch mechanism when removing the column.
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_column("received_at")
