"""lifesync_4_workflows_and_projects

Revision ID: e4a2c10b78d3
Revises: dd19a46448f2
Create Date: 2026-11-21 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e4a2c10b78d3'
down_revision: Union[str, None] = 'dd19a46448f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Projects Table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role_context', sa.String(length=50), nullable=False, server_default='professional', index=True),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='active', index=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('notes', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('decisions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. Workflow Executions Table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending', index=True),
        sa.Column('plan_graph', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('context_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('current_step_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. Workflow Step Executions Table
    op.create_table(
        'workflow_step_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflow_executions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('step_id', sa.String(length=80), nullable=False, index=True),
        sa.Column('step_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('agent_name', sa.String(length=80), nullable=False),
        sa.Column('tool_name', sa.String(length=80), nullable=False),
        sa.Column('input_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('output_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('depends_on', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending', index=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approval_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('action_approvals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 4. Foreign Key Columns on Tasks, Goals, Memories, and Knowledge Documents
    op.add_column('tasks', sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True))
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)

    op.add_column('goals', sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True))
    op.create_index(op.f('ix_goals_project_id'), 'goals', ['project_id'], unique=False)

    op.add_column('memories', sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True))
    op.create_index(op.f('ix_memories_project_id'), 'memories', ['project_id'], unique=False)

    op.add_column('knowledge_documents', sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True))
    op.create_index(op.f('ix_knowledge_documents_project_id'), 'knowledge_documents', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_knowledge_documents_project_id'), table_name='knowledge_documents')
    op.drop_column('knowledge_documents', 'project_id')

    op.drop_index(op.f('ix_memories_project_id'), table_name='memories')
    op.drop_column('memories', 'project_id')

    op.drop_index(op.f('ix_goals_project_id'), table_name='goals')
    op.drop_column('goals', 'project_id')

    op.drop_index(op.f('ix_tasks_project_id'), table_name='tasks')
    op.drop_column('tasks', 'project_id')

    op.drop_table('workflow_step_executions')
    op.drop_table('workflow_executions')
    op.drop_table('projects')
