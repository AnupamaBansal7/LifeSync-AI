"""Create model_configs view pointing to model_configurations

Revision ID: d4f6b8c0e2a4
Revises: c3e5a7b9d1f3
Create Date: 2026-11-23 00:29:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4f6b8c0e2a4'
down_revision: Union[str, None] = 'c3e5a7b9d1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE OR REPLACE VIEW model_configs AS SELECT * FROM model_configurations;")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS model_configs;")
