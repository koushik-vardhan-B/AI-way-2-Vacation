"""add conversation history to travel plans

Revision ID: conv_history_001
Revises: 90e5d5f3952b
Create Date: 2025-10-27 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'conv_history_001'
down_revision = '90e5d5f3952b'
branch_labels = None
depends_on = None


def upgrade():
    """Add conversation_history and thread_id columns to travel_plans table"""
    # Add conversation_history column (JSON type)
    op.add_column('travel_plans', sa.Column('conversation_history', sa.JSON(), nullable=True))
    
    # Add thread_id column (String type)
    op.add_column('travel_plans', sa.Column('thread_id', sa.String(length=255), nullable=True))


def downgrade():
    """Remove conversation_history and thread_id columns from travel_plans table"""
    op.drop_column('travel_plans', 'thread_id')
    op.drop_column('travel_plans', 'conversation_history')
