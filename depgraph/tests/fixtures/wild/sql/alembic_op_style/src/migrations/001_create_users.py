"""Alembic-style migration — uses op.create_table(), not text().

This file intentionally has NO text() calls. is_migration_file() returns False
and extract_migration() is never called on it. Zero schema primitives result.
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("users")
