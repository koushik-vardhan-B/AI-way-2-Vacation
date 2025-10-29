"""add location_data to travel_plans

Revision ID: add_location_data
Revises: add_conversation_history_to_travel_plans
Create Date: 2025-10-28 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_location_data'
down_revision = 'add_conversation_history_to_travel_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add location_data column to travel_plans table"""
    # Add location_data column
    op.add_column('travel_plans', sa.Column('location_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove location_data column from travel_plans table"""
    op.drop_column('travel_plans', 'location_data')
