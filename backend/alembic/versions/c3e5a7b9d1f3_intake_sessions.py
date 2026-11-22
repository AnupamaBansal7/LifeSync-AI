"""intake_sessions

Revision ID: c3e5a7b9d1f3
Revises: b2d4e6f8a0c2
Create Date: 2026-11-22 23:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c3e5a7b9d1f3'
down_revision: Union[str, None] = 'b2d4e6f8a0c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'intake_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('initial_prompt', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=40), nullable=False, server_default='GENERAL'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='GATHERING_INFO', index=True),
        sa.Column('collected_context_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_steps', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('resulting_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transaction_plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('intake_sessions')
